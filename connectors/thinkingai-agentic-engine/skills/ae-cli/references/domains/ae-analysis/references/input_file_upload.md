# analysis input-file upload

Upload a local file to the analysis gateway for a declared purpose and return an `input_file_id`.

```bash
ae-cli analysis input-file upload --project-id <project_id> --purpose <purpose> --file <local_path>
```

Call `analysis input-file purpose list` first and copy a returned purpose. Do not invent a purpose or use this low-level command when `user-tag create-id --input-file` or `user-cluster create-id --input-file` can perform the upload automatically.

The response returns an owner/project/purpose-bound `ifile_...` identifier and inspection metadata.
