import { Resource } from 'fastmcp';
import { getGodotConnection } from '../utils/godot_connection.js';

/**
 * Resource that provides information about the current state of the Godot editor
 */
export const editorStateResource: Resource = {
  uri: 'godot/editor/state',
  name: 'Godot Editor State',
  mimeType: 'application/json',
  async load() {
    const godot = getGodotConnection();
    
    try {
      // Call a command on the Godot side to get editor state
      const result = await godot.sendCommand('get_editor_state');
      
      return {
        text: JSON.stringify(result)
      };
    } catch (error) {
      console.error('Error fetching editor state:', error);
      throw error;
    }
  }
};

/**
 * Resource that provides information about the currently selected node
 */
export const selectedNodeResource: Resource = {
  uri: 'godot/editor/selected_node',
  name: 'Godot Selected Node',
  mimeType: 'application/json',
  async load() {
    const godot = getGodotConnection();
    
    try {
      // Call a command on the Godot side to get selected node
      const result = await godot.sendCommand('get_selected_node');
      
      return {
        text: JSON.stringify(result)
      };
    } catch (error) {
      console.error('Error fetching selected node:', error);
      throw error;
    }
  }
};

/**
 * Resource that provides information about the currently edited script
 */
export const currentScriptResource: Resource = {
  uri: 'godot/editor/current_script',
  name: 'Current Script in Editor',
  mimeType: 'text/plain',
  async load() {
    const godot = getGodotConnection();
    
    try {
      // Call a command on the Godot side to get current script
      const result = await godot.sendCommand('get_current_script');
      
      // If we got a script path, return script content and metadata
      if (result && result.script_found && result.content) {
        return {
          text: result.content,
          metadata: {
            path: result.script_path,
            language: result.script_path.endsWith('.gd') ? 'gdscript' : 
                     result.script_path.endsWith('.cs') ? 'csharp' : 'unknown'
          }
        };
      } else {
        return {
          text: '',
          metadata: {
            error: 'No script currently being edited',
            script_found: false
          }
        };
      }
    } catch (error) {
      console.error('Error fetching current script:', error);
      throw error;
    }
  }
};