export const COLLECTION_EVENT_BINDING_ERROR = 'COLLECTION_CURRENT_RUN_EVENT_BINDING_MISSING'

function sameSet(left, right) {
  return left.size === right.size && [...left].every((value) => right.has(value))
}

function eventInSeatScope(event, status) {
  return event.metadata?.agendaItemId === status.agendaItemId
    && event.metadata?.seatId === status.seatId
    && event.metadata?.revision === status.revision
}

function eventBeforeSeal(events, seal, predicate) {
  return events.some((event) => event.sequence < seal.sequence && predicate(event))
}

export function bindCollectionStatusesToCurrentRunEvents({ events, plan, statuses, planPayloadHash }) {
  const expectedSeatIds = new Set([...plan.specialistSeatIds, ...plan.supportSeatIds])
  return statuses.map((status) => {
    if (!['accepted', 'unavailable_after_retry'].includes(status.status)) return status
    const seal = events.find((event) => event.eventType === 'round.independent_sealed'
      && event.metadata?.agendaItemId === status.agendaItemId
      && event.metadata?.revision === status.revision)
    if (!seal) return { ...status, status: 'awaiting_current_run_event', errorCode: COLLECTION_EVENT_BINDING_ERROR }

    const selectedBeforeSeal = new Set(events
      .filter((event) => event.sequence < seal.sequence
        && event.eventType === 'seat.selected'
        && event.metadata?.agendaItemId === status.agendaItemId
        && event.metadata?.revision === status.revision)
      .map((event) => event.metadata.seatId))
    const lateSeatEvent = events.some((event) => event.sequence > seal.sequence
      && event.eventType.startsWith('seat.')
      && event.metadata?.agendaItemId === status.agendaItemId
      && event.metadata?.revision === status.revision)
    const planEventBound = eventBeforeSeal(events, seal, (event) => event.eventType === 'plan.frozen'
      && event.metadata?.revision === plan.revision && event.payloadHash === planPayloadHash)
    const dispatchRequested = eventBeforeSeal(events, seal, (event) => event.eventType === 'seat.dispatch_requested'
      && eventInSeatScope(event, status) && event.payloadHash === status.taskPayloadHash)
    const dispatched = eventBeforeSeal(events, seal, (event) => event.eventType === 'seat.dispatched'
      && eventInSeatScope(event, status) && event.payloadHash === status.taskPayloadHash)
    const dispatchFailed = eventBeforeSeal(events, seal, (event) => event.eventType === 'seat.dispatch_failed'
      && eventInSeatScope(event, status) && event.payloadHash === status.taskPayloadHash)
    const terminalBound = status.status === 'accepted'
      ? dispatched && eventBeforeSeal(events, seal, (event) => ['seat.result_received', 'seat.result_recovered'].includes(event.eventType)
        && eventInSeatScope(event, status) && event.payloadHash === status.resultPayloadHash)
      : (dispatched || dispatchFailed) && eventBeforeSeal(events, seal, (event) => event.eventType === 'seat.result_failed'
        && eventInSeatScope(event, status) && event.payloadHash === status.failurePayloadHash)
    if (sameSet(selectedBeforeSeal, expectedSeatIds) && !lateSeatEvent && planEventBound && dispatchRequested && terminalBound) return status
    return { ...status, status: 'awaiting_current_run_event', errorCode: COLLECTION_EVENT_BINDING_ERROR }
  })
}
