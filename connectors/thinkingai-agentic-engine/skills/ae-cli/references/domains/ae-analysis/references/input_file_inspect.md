# analysis input-file inspect

Inspect an uploaded analysis input file owned by the current user.

```bash
ae-cli analysis input-file inspect --input-file-id <ifile_id>
```

Do not use this command to read file content or inspect another user's file. The response returns descriptor metadata; ownership mismatches fail as `INPUT_FILE_NOT_FOUND`.
