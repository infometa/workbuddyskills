# analysis input-file purpose list

List input-file purposes the current identity may upload in one project.

```bash
ae-cli analysis input-file purpose list --project-id <project_id>
```

Use this before the low-level upload command. Do not guess purpose strings. The response returns each purpose's analysis gateway domain, formats, size limit, and consuming capabilities.
