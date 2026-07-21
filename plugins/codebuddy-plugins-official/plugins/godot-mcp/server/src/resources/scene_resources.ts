import { Resource, ResourceTemplate } from 'fastmcp';
import { getGodotConnection } from '../utils/godot_connection.js';
import { z } from 'zod';

/**
 * Resource that provides a list of all scenes in the project
 */
export const sceneListResource: Resource = {
  uri: 'godot/scenes',
  name: 'Godot Scene List',
  mimeType: 'application/json',
  async load() {
    const godot = getGodotConnection();
    
    try {
      // Call a command on the Godot side to list all scenes
      const result = await godot.sendCommand('list_project_files', {
        extensions: ['.tscn', '.scn']
      });
      
      if (result && result.files) {
        return {
          text: JSON.stringify({
            scenes: result.files,
            count: result.files.length
          })
        };
      } else {
        return {
          text: JSON.stringify({
            scenes: [],
            count: 0
          })
        };
      }
    } catch (error) {
      console.error('Error fetching scene list:', error);
      throw error;
    }
  }
};

/**
 * Resource that provides detailed information about the current scene
 */
export const sceneStructureResource: Resource = {
    uri: 'godot/scene/current',
    name: 'Godot Current Scene',
    mimeType: 'application/json',
    async load() {
        const godot = getGodotConnection();
        
        try {
            // Get current scene info first
            const sceneInfo = await godot.sendCommand('get_current_scene', {});
            
            // If we have a valid scene path, get its structure
            if (sceneInfo && sceneInfo.scene_path && sceneInfo.scene_path !== 'None' && sceneInfo.scene_path !== 'Untitled') {
                try {
                    const structure = await godot.sendCommand('get_scene_structure', { path: sceneInfo.scene_path });
                    return {
                        text: JSON.stringify({
                            ...sceneInfo,
                            structure: structure.structure
                        })
                    };
                } catch {
                    // If structure fetch fails, return basic info
                    return {
                        text: JSON.stringify(sceneInfo)
                    };
                }
            }
            
            return {
                text: JSON.stringify(sceneInfo)
            };
        } catch (error) {
            console.error('Error fetching current scene:', error);
            throw error;
        }
    }
};
