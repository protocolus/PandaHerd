import zipfile
from xml.etree import ElementTree as ET
import io
import os
from PIL import Image
import math
import json
from typing import Optional, Dict, Any, Tuple, List

class ThreeMFAnalyzer:
    """Analyzer for 3MF files to extract metadata, thumbnails, and print settings"""
    
    def __init__(self, file_path: str = None, file_content: bytes = None):
        """Initialize analyzer with either a file path or file content"""
        self.file_path = file_path
        self.file_content = file_content
        self.zip_file = None
        self.metadata = {}
        
    def __enter__(self):
        """Context manager entry"""
        if self.file_path:
            self.zip_file = zipfile.ZipFile(self.file_path)
        else:
            self.zip_file = zipfile.ZipFile(io.BytesIO(self.file_content))
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.zip_file:
            self.zip_file.close()
            
    def get_thumbnail(self) -> Optional[bytes]:
        """Extract thumbnail from 3MF file"""
        try:
            # Check common thumbnail paths
            thumbnail_paths = [
                'Metadata/thumbnail.png',
                'Metadata/thumbnail.jpg',
                'thumbnail.png',
                'thumbnail.jpg'
            ]
            
            for path in thumbnail_paths:
                try:
                    return self.zip_file.read(path)
                except KeyError:
                    continue
                    
            return None
        except Exception as e:
            print(f"Error extracting thumbnail: {e}")
            return None
            
    def get_model_info(self) -> Dict[str, Any]:
        """Extract model information from 3MF file"""
        try:
            # Read 3D model data
            model_data = self.zip_file.read('3D/3dmodel.model')
            root = ET.fromstring(model_data)
            
            # Extract namespace for proper XML parsing
            ns = {'': root.tag.split('}')[0][1:]} if '}' in root.tag else {}
            
            # Find all mesh objects
            objects = root.findall('.//mesh', ns)
            
            total_vertices = 0
            total_triangles = 0
            min_x = min_y = min_z = float('inf')
            max_x = max_y = max_z = float('-inf')
            
            # Analyze each mesh
            for mesh in objects:
                vertices = mesh.findall('.//vertex', ns)
                triangles = mesh.findall('.//triangle', ns)
                
                total_vertices += len(vertices)
                total_triangles += len(triangles)
                
                # Calculate bounding box
                for vertex in vertices:
                    x = float(vertex.get('x'))
                    y = float(vertex.get('y'))
                    z = float(vertex.get('z'))
                    
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    min_z = min(min_z, z)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                    max_z = max(max_z, z)
            
            # Calculate dimensions in mm
            dimensions = {
                'width': round(max_x - min_x, 2),
                'depth': round(max_y - min_y, 2),
                'height': round(max_z - min_z, 2)
            }
            
            # Calculate volume (approximate)
            volume = dimensions['width'] * dimensions['depth'] * dimensions['height']
            
            return {
                'vertices': total_vertices,
                'triangles': total_triangles,
                'dimensions': dimensions,
                'volume_cm3': round(volume / 1000, 2),  # Convert to cm³
                'estimated_print_time': self._estimate_print_time(total_triangles, volume),
                'estimated_material_grams': self._estimate_material_weight(volume)
            }
        except Exception as e:
            print(f"Error analyzing model: {e}")
            return {}
            
    def get_print_settings(self) -> Dict[str, Any]:
        """Extract print settings from 3MF file"""
        try:
            # Try to find print settings file (varies by slicer)
            setting_files = [
                'Metadata/print_settings.xml',
                'Metadata/slice_settings.xml',
                'print_settings.xml'
            ]
            
            settings = {}
            
            for file in setting_files:
                try:
                    data = self.zip_file.read(file)
                    root = ET.fromstring(data)
                    
                    # Extract basic settings (customize based on your needs)
                    settings.update({
                        'layer_height': self._find_setting(root, 'layer_height'),
                        'infill_density': self._find_setting(root, 'infill_density'),
                        'material': self._find_setting(root, 'material'),
                        'nozzle_temperature': self._find_setting(root, 'nozzle_temperature'),
                        'bed_temperature': self._find_setting(root, 'bed_temperature')
                    })
                    
                    break
                except KeyError:
                    continue
                    
            return settings
        except Exception as e:
            print(f"Error extracting print settings: {e}")
            return {}
    
    def _find_setting(self, root: ET.Element, setting_name: str) -> Optional[str]:
        """Helper to find a setting in the XML tree"""
        # Try different common XML paths and attribute names
        paths = [
            f".//{setting_name}",
            f".//setting[@name='{setting_name}']",
            f".//parameter[@name='{setting_name}']"
        ]
        
        for path in paths:
            element = root.find(path)
            if element is not None:
                return element.get('value') or element.text
                
        return None
    
    def _estimate_print_time(self, triangles: int, volume: float) -> str:
        """Rough estimate of print time based on model complexity and volume"""
        # This is a very rough estimation - real print time depends on many factors
        base_time = math.sqrt(triangles) * 0.1  # Basic complexity factor
        volume_factor = volume / 1000  # Volume in cm³
        
        total_minutes = base_time + (volume_factor * 10)  # Rough estimate
        
        hours = int(total_minutes / 60)
        minutes = int(total_minutes % 60)
        
        return f"{hours}h {minutes}m"
    
    def _estimate_material_weight(self, volume: float) -> float:
        """Rough estimate of material weight based on volume"""
        # Assume 20% infill and PLA density of 1.24 g/cm³
        infill_factor = 0.2
        density = 1.24  # g/cm³
        
        volume_cm3 = volume / 1000  # Convert to cm³
        weight = volume_cm3 * density * infill_factor
        
        return round(weight, 2)
    
    def get_bambu_metadata(self) -> Dict[str, Any]:
        """Extract Bambu Lab specific metadata including AMS mappings"""
        try:
            # Common paths for Bambu metadata
            metadata_paths = [
                'Metadata/plate_1.json',
                'Metadata/slice_info.json',
                'plate_1.json',
                'slice_info.json'
            ]
            
            for path in metadata_paths:
                try:
                    data = self.zip_file.read(path)
                    metadata = json.loads(data)
                    
                    # Extract AMS mappings
                    ams_mapping = self._extract_ams_mapping(metadata)
                    if ams_mapping:
                        return {
                            "ams_mapping": ams_mapping,
                            "plate_info": self._extract_plate_info(metadata),
                            "print_params": self._extract_print_params(metadata)
                        }
                except KeyError:
                    continue
                    
            return {}
        except Exception as e:
            print(f"Error extracting Bambu metadata: {e}")
            return {}
            
    def _extract_ams_mapping(self, metadata: Dict) -> List[Dict[str, Any]]:
        """Extract AMS mapping information from metadata"""
        try:
            # Handle different metadata formats
            if "filament_info" in metadata:
                # Newer format
                filaments = metadata["filament_info"]
                return [
                    {
                        "ams_slot": filament.get("tray_id", i),
                        "type": filament.get("type", "PLA"),
                        "color": filament.get("color", "#FFFFFF"),
                        "temperature": filament.get("nozzle_temperature_initial_layer", 200),
                        "weight_used": filament.get("used_weight", 0),
                        "name": filament.get("name", f"Filament {i+1}")
                    }
                    for i, filament in enumerate(filaments)
                ]
            elif "ams_mapping" in metadata:
                # Older format
                mappings = metadata["ams_mapping"]
                return [
                    {
                        "ams_slot": mapping.get("slot", i),
                        "type": mapping.get("filament_type", "PLA"),
                        "color": mapping.get("color", "#FFFFFF"),
                        "temperature": mapping.get("nozzle_temp", 200),
                        "name": mapping.get("filament_name", f"Filament {i+1}")
                    }
                    for i, mapping in enumerate(mappings)
                ]
            
            return []
        except Exception as e:
            print(f"Error extracting AMS mapping: {e}")
            return []
            
    def _extract_plate_info(self, metadata: Dict) -> Dict[str, Any]:
        """Extract plate-specific information"""
        try:
            return {
                "plate_type": metadata.get("plate_type", "smooth"),
                "bed_temp": metadata.get("bed_temp", 60),
                "chamber_temp": metadata.get("chamber_temp", 0),
                "first_layer_bed_temp": metadata.get("first_layer_bed_temp", 60)
            }
        except Exception:
            return {}
            
    def _extract_print_params(self, metadata: Dict) -> Dict[str, Any]:
        """Extract print parameters"""
        try:
            return {
                "layer_height": metadata.get("layer_height", 0.2),
                "initial_layer_height": metadata.get("initial_layer_height", 0.2),
                "perimeters": metadata.get("perimeters", 3),
                "infill_density": metadata.get("infill_density", 20),
                "support_type": metadata.get("support_type", "normal"),
                "enable_support": metadata.get("enable_support", False),
                "brim_type": metadata.get("brim_type", "no_brim"),
                "brim_width": metadata.get("brim_width", 0)
            }
        except Exception:
            return {}

    def analyze(self) -> Dict[str, Any]:
        """Perform full analysis of the 3MF file"""
        thumbnail = self.get_thumbnail()
        model_info = self.get_model_info()
        print_settings = self.get_print_settings()
        bambu_metadata = self.get_bambu_metadata()
        
        return {
            'has_thumbnail': thumbnail is not None,
            'thumbnail': thumbnail,
            'model_info': model_info,
            'print_settings': print_settings,
            'bambu_metadata': bambu_metadata
        }
