# Streaming Responses in Route Handlers

## Basic Streaming

### Using ReadableStream

```tsx
// app/api/stream/route.ts
export async function GET() {
  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      for (let i = 0; i < 10; i++) {
        const chunk = encoder.encode(`Chunk ${i}\n`)
        controller.enqueue(chunk)
        await new Promise(resolve => setTimeout(resolve, 500))
      }
      controller.close()
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Transfer-Encoding': 'chunked',
    },
  })
}
```

### Streaming JSON Lines

```tsx
// app/api/stream-json/route.ts
export async function GET() {
  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      const items = await fetchLargeDataset()

      for (const item of items) {
        const json = JSON.stringify(item) + '\n'
        controller.enqueue(encoder.encode(json))
      }

      controller.close()
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'application/x-ndjson',
    },
  })
}
```

## Server-Sent Events (SSE)

### Basic SSE

```tsx
// app/api/sse/route.ts
export async function GET() {
  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      let count = 0

      const interval = setInterval(() => {
        const data = `data: ${JSON.stringify({ count: count++, time: new Date().toISOString() })}\n\n`
        controller.enqueue(encoder.encode(data))

        if (count >= 10) {
          clearInterval(interval)
          controller.close()
        }
      }, 1000)
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}
```

### SSE with Event Types

```tsx
// app/api/events/route.ts
export async function GET() {
  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      // Send a named event
      const sendEvent = (eventType: string, data: unknown) => {
        const message = `event: ${eventType}\ndata: ${JSON.stringify(data)}\n\n`
        controller.enqueue(encoder.encode(message))
      }

      // Initial connection event
      sendEvent('connected', { status: 'ok' })

      // Simulate notifications
      const notifications = await getNotifications()
      for (const notification of notifications) {
        sendEvent('notification', notification)
        await delay(500)
      }

      // Final event
      sendEvent('complete', { total: notifications.length })
      controller.close()
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}
```

### Client-Side SSE Consumer

```tsx
// components/sse-consumer.tsx
'use client'

import { useEffect, useState } from 'react'

interface Event {
  type: string
  data: unknown
}

export function SSEConsumer() {
  const [events, setEvents] = useState<Event[]>([])
  const [status, setStatus] = useState('disconnected')

  useEffect(() => {
    const eventSource = new EventSource('/api/events')

    eventSource.onopen = () => {
      setStatus('connected')
    }

    eventSource.addEventListener('notification', (event) => {
      const data = JSON.parse(event.data)
      setEvents(prev => [...prev, { type: 'notification', data }])
    })

    eventSource.addEventListener('complete', (event) => {
      const data = JSON.parse(event.data)
      setEvents(prev => [...prev, { type: 'complete', data }])
      eventSource.close()
    })

    eventSource.onerror = () => {
      setStatus('error')
      eventSource.close()
    }

    return () => {
      eventSource.close()
    }
  }, [])

  return (
    <div>
      <p>Status: {status}</p>
      <ul>
        {events.map((event, i) => (
          <li key={i}>{JSON.stringify(event)}</li>
        ))}
      </ul>
    </div>
  )
}
```

## Streaming with AI/LLM

### OpenAI Streaming

```tsx
// app/api/chat/route.ts
import OpenAI from 'openai'

const openai = new OpenAI()

export async function POST(request: Request) {
  const { messages } = await request.json()

  const response = await openai.chat.completions.create({
    model: 'gpt-4',
    messages,
    stream: true,
  })

  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      for await (const chunk of response) {
        const content = chunk.choices[0]?.delta?.content || ''
        controller.enqueue(encoder.encode(content))
      }
      controller.close()
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
    },
  })
}
```

### Vercel AI SDK

```tsx
// app/api/chat/route.ts
import { openai } from '@ai-sdk/openai'
import { streamText } from 'ai'

export async function POST(request: Request) {
  const { messages } = await request.json()

  const result = streamText({
    model: openai('gpt-4'),
    messages,
  })

  return result.toDataStreamResponse()
}
```

## File Downloads

### Streaming Large Files

```tsx
// app/api/download/[filename]/route.ts
import { createReadStream } from 'fs'
import { stat } from 'fs/promises'
import path from 'path'
import { Readable } from 'stream'

export async function GET(
  request: Request,
  { params }: { params: Promise<{ filename: string }> }
) {
  const { filename } = await params
  const filepath = path.join(process.cwd(), 'files', filename)

  const stats = await stat(filepath)
  const fileStream = createReadStream(filepath)

  // Convert Node.js stream to Web ReadableStream
  const stream = Readable.toWeb(fileStream) as ReadableStream

  return new Response(stream, {
    headers: {
      'Content-Type': 'application/octet-stream',
      'Content-Disposition': `attachment; filename="${filename}"`,
      'Content-Length': stats.size.toString(),
    },
  })
}
```

### Range Requests (Video Streaming)

```tsx
// app/api/video/[id]/route.ts
import { createReadStream } from 'fs'
import { stat } from 'fs/promises'
import path from 'path'

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const filepath = path.join(process.cwd(), 'videos', `${id}.mp4`)
  const stats = await stat(filepath)
  const fileSize = stats.size

  const range = request.headers.get('range')

  if (range) {
    const parts = range.replace(/bytes=/, '').split('-')
    const start = parseInt(parts[0], 10)
    const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1
    const chunkSize = end - start + 1

    const fileStream = createReadStream(filepath, { start, end })
    const stream = Readable.toWeb(fileStream) as ReadableStream

    return new Response(stream, {
      status: 206,
      headers: {
        'Content-Range': `bytes ${start}-${end}/${fileSize}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunkSize.toString(),
        'Content-Type': 'video/mp4',
      },
    })
  }

  const fileStream = createReadStream(filepath)
  const stream = Readable.toWeb(fileStream) as ReadableStream

  return new Response(stream, {
    headers: {
      'Content-Length': fileSize.toString(),
      'Content-Type': 'video/mp4',
    },
  })
}
```

## Progress Tracking

### Upload Progress

```tsx
// app/api/upload-progress/route.ts
export async function POST(request: Request) {
  const contentLength = parseInt(request.headers.get('content-length') || '0')
  const reader = request.body?.getReader()

  if (!reader) {
    return new Response('No body', { status: 400 })
  }

  let receivedLength = 0
  const chunks: Uint8Array[] = []

  while (true) {
    const { done, value } = await reader.read()

    if (done) break

    chunks.push(value)
    receivedLength += value.length

    const progress = Math.round((receivedLength / contentLength) * 100)
    console.log(`Progress: ${progress}%`)
  }

  // Combine chunks
  const data = new Uint8Array(receivedLength)
  let position = 0
  for (const chunk of chunks) {
    data.set(chunk, position)
    position += chunk.length
  }

  return new Response(JSON.stringify({ received: receivedLength }))
}
```

## Async Iteration

### Database Cursor Streaming

```tsx
// app/api/export/route.ts
export async function GET() {
  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      // Header row
      controller.enqueue(encoder.encode('id,name,email\n'))

      // Stream results from database cursor
      const cursor = db.user.findMany({
        cursor: { id: 'start' },
        take: 100,
      })

      for await (const batch of cursor) {
        for (const user of batch) {
          const row = `${user.id},${user.name},${user.email}\n`
          controller.enqueue(encoder.encode(row))
        }
      }

      controller.close()
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/csv',
      'Content-Disposition': 'attachment; filename="users.csv"',
    },
  })
}
```

## Error Handling in Streams

```tsx
// app/api/stream-safe/route.ts
export async function GET() {
  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      try {
        for await (const item of fetchItems()) {
          controller.enqueue(encoder.encode(JSON.stringify(item) + '\n'))
        }
        controller.close()
      } catch (error) {
        // Send error as part of stream before closing
        controller.enqueue(
          encoder.encode(JSON.stringify({ error: 'Stream failed' }) + '\n')
        )
        controller.close()
      }
    },
    cancel(reason) {
      console.log('Stream cancelled:', reason)
      // Cleanup resources
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'application/x-ndjson',
    },
  })
}
```

## TransformStream

### Transform Data On-the-Fly

```tsx
// app/api/transform/route.ts
export async function POST(request: Request) {
  const { readable, writable } = new TransformStream({
    transform(chunk, controller) {
      // Transform each chunk (e.g., uppercase text)
      const text = new TextDecoder().decode(chunk)
      const transformed = text.toUpperCase()
      controller.enqueue(new TextEncoder().encode(transformed))
    },
  })

  // Pipe input through transform
  request.body?.pipeTo(writable)

  return new Response(readable, {
    headers: {
      'Content-Type': 'text/plain',
    },
  })
}
```
