import { Resource, ResourceTemplate } from 'fastmcp';
import { getGodotConnection } from '../utils/godot_connection.js';
import { z } from 'zod';

/**
 * Resource that provides the content of the currently edited script
 */
export const scriptResource: Resource = {
    uri: 'godot/script',
    name: 'Godot Current Script Content',
    mimeType: 'text/plain',
    async load() {
        const godot = getGodotConnection();
        
        try {
            // Get the currently edited script in the editor
            const result = await godot.sendCommand('get_current_script', {});
            
            if (!result.script_found) {
                return {
                    text: '',
                    metadata: {
                        error: 'No script currently being edited',
                        script_found: false
                    }
                };
            }
            
            return {
                text: result.content,
                metadata: {
                    path: result.script_path,
                    language: result.script_path.endsWith('.gd') ? 'gdscript' : 
                             result.script_path.endsWith('.cs') ? 'csharp' : 'unknown'
                }
            };
        } catch (error) {
            console.error('Error fetching current script:', error);
            throw error;
        }
    }
};

/**
 * Resource that provides a list of all scripts in the project
 */
export const scriptListResource: Resource = {
  uri: 'godot/scripts',
  name: 'Godot Script List',
  mimeType: 'application/json',
  async load() {
    const godot = getGodotConnection();
    
    try {
      // Call a command on the Godot side to list all scripts
      const result = await godot.sendCommand('list_project_files', {
        extensions: ['.gd', '.cs']
      });
      
      if (result && result.files) {
        return {
          text: JSON.stringify({
            scripts: result.files,
            count: result.files.length,
            gdscripts: result.files.filter((f: string) => f.endsWith('.gd')),
            csharp_scripts: result.files.filter((f: string) => f.endsWith('.cs'))
          })
        };
      } else {
        return {
          text: JSON.stringify({
            scripts: [],
            count: 0,
            gdscripts: [],
            csharp_scripts: []
          })
        };
      }
    } catch (error) {
      console.error('Error fetching script list:', error);
      throw error;
    }
  }
};

/**
 * Resource that provides metadata for the currently edited script
 */
export const scriptMetadataResource: Resource = {
    uri: 'godot/script/metadata',
    name: 'Godot Current Script Metadata',
    mimeType: 'application/json',
    async load() {
        const godot = getGodotConnection();
        
        try {
            // First get the current script path
            const currentScript = await godot.sendCommand('get_current_script', {});
            
            if (!currentScript.script_found || !currentScript.script_path) {
                return {
                    text: JSON.stringify({
                        error: 'No script currently being edited',
                        script_found: false
                    })
                };
            }
            
            // Get metadata for the current script
            const result = await godot.sendCommand('get_script_metadata', {
                path: currentScript.script_path
            });
            
            return {
                text: JSON.stringify(result)
            };
        } catch (error) {
            console.error('Error fetching script metadata:', error);
            throw error;
        }
    }
};
