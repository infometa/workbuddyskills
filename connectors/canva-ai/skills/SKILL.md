---
name: canva
description: "Use Canva's design capabilities: create and edit designs, manage assets and brand resources, search the asset library, export designs, and add comments."
description_zh: "让AI助手无缝调用Canva可画的设计能力，包括创建设计、编辑设计、管理素材和品牌资源、搜索资源库、导出设计以及添加评论等。"
description_en: "Access Canva's design capabilities: design creation and editing, asset and brand management, search, export, commenting, and more."
version: "1.0.0"
---

# Canva Skill

Connecting to Canva via the MCP protocol allows AI to seamlessly access design capabilities, including creating and editing designs, managing materials and brand resources, searching the resource library, exporting designs, and adding comments.

## Functionality

- **Design Creation**: Using natural language descriptions, AI automatically creates design drafts in Canva.
- **Editing and Designing**: Modifying and adjusting existing designs.
- **Material and Brand Management**: Managing material libraries and brand resources
- **Resource Search**: Search for templates and resources in the Canva drawing library.
- **Export Design**: Export your design as an image or other format.
- **Comment Management**: Add comments and feedback to your designs.

## Calling Principles

1. Ensure that the Canva drawing MCP service is correctly configured and accessible.
2. When creating a design, provide as much detail as possible regarding your requirements, including design type, style, dimensions, etc.
3. Clearly specify the target design and modification content when editing the design.
4. Specify the required format and dimensions when exporting the design.

## Typical Process

1. **Design Creation**: Describe requirements → Create design in Canva using AI → View results → Iterate and modify.
2. **Design Editing**: Specify design → Describe modification requirements → Perform modifications in AI → Confirm results
3. **Design Export**: Specify design → Select export format → AI (AI) → Obtain results

## Error Handling

- If the connection fails, check if the MCP service address is correct.
- If you are unable to create a design, please verify that the design parameters are complete.
- If export fails, check if the design is complete and if the format parameters are correct.
