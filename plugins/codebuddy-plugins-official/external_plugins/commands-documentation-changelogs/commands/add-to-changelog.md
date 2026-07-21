---
description: Add a new entry to the project's CHANGELOG.md file following Keep a Changelog format
category: documentation-changelogs
argument-hint: <version> <change_type> <message>
allowed-tools: Read, Edit
---

# Update Changelog

Add a new entry to the project's CHANGELOG.md file based on the provided arguments.

## Parse Arguments

Parse $ARGUMENTS to extract:
- Version number (e.g., "1.1.0")
- Change type: "added", "changed", "deprecated", "removed", "fixed", or "security"
- `<message>` is the description of the change

## Examples

```
/add-to-changelog 1.1.0 added "New markdown to BlockDoc conversion feature"
```

```
/add-to-changelog 1.0.2 fixed "Bug in HTML renderer causing incorrect output"
```

## Description

This command will:

1. Check if a CHANGELOG.md file exists and create one if needed
2. Look for an existing section for the specified version
   - If found, add the new entry under the appropriate change type section
   - If not found, create a new version section with today's date
3. Format the entry according to Keep a Changelog conventions
4. Commit the changes if requested

The CHANGELOG follows the [Keep a Changelog](https://keepachangelog.com/) format and [Semantic Versioning](https://semver.org/).

## Implementation

The command should:

1. Parse the arguments to extract version, change type, and message
2. Read the existing CHANGELOG.md file if it exists
3. If the file doesn't exist, create a new one with standard header
4. Check if the version section already exists
5. Add the new entry in the appropriate section
6. Write the updated content back to the file
7. Suggest committing the changes

Remember to update the package version in `__init__.py` and `setup.py` if this is a new version.