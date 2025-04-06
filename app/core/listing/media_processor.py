from typing import Dict, List, Optional
import logging
import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import rembg
from moviepy.editor import ImageSequenceClip
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class MediaProcessor:
    """Service for processing listing media files."""
    
    def __init__(self):
        """Initialize the media processor."""
        self.output_dir = os.getenv("MEDIA_OUTPUT_DIR", "media/output")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_images(self,
                      image_files: List[str],
                      options: Dict) -> List[str]:
        """Process images with enhancements.
        
        Args:
            image_files: List of image file paths
            options: Processing options dictionary
            
        Returns:
            List of processed image file paths
        """
        try:
            processed_files = []
            
            for image_file in image_files:
                if not image_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                
                # Load image
                image = Image.open(image_file)
                
                # Remove background if requested
                if options.get("remove_background", False):
                    image = self._remove_background(image)
                
                # Apply color correction if requested
                if options.get("color_correction", False):
                    image = self._correct_colors(image)
                
                # Add watermark if requested
                if options.get("add_watermark", False):
                    image = self._add_watermark(image)
                
                # Save processed image
                output_file = os.path.join(
                    self.output_dir,
                    f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(image_file)}"
                )
                image.save(output_file)
                
                processed_files.append(output_file)
            
            return processed_files
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return image_files
    
    def generate_video(self,
                      image_files: List[str],
                      options: Dict) -> str:
        """Generate product video.
        
        Args:
            image_files: List of image file paths
            options: Video generation options dictionary
            
        Returns:
            Path to generated video file
        """
        try:
            if not image_files:
                return ""
            
            # Process images for video
            processed_images = []
            for image_file in image_files:
                if not image_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                
                # Load image
                image = cv2.imread(image_file)
                
                # Remove background
                image = self._remove_background_cv2(image)
                
                # Apply color correction
                image = self._correct_colors_cv2(image)
                
                processed_images.append(image)
            
            if not processed_images:
                return ""
            
            # Generate 360° spin frames
            frames = self._generate_spin_frames(processed_images[0])
            
            # Create video clip
            clip = ImageSequenceClip(frames, fps=30)
            
            # Save video
            output_file = os.path.join(
                self.output_dir,
                f"product_spin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            )
            clip.write_videofile(output_file)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return ""
    
    def _remove_background(self, image: Image.Image) -> Image.Image:
        """Remove background from image using rembg.
        
        Args:
            image: PIL Image object
            
        Returns:
            Processed PIL Image object
        """
        try:
            # Convert to bytes
            img_byte_arr = image.tobytes()
            
            # Remove background
            output = rembg.remove(img_byte_arr)
            
            # Convert back to PIL Image
            return Image.frombytes(image.mode, image.size, output)
            
        except Exception as e:
            logger.error(f"Background removal failed: {e}")
            return image
    
    def _remove_background_cv2(self, image: np.ndarray) -> np.ndarray:
        """Remove background from image using OpenCV.
        
        Args:
            image: OpenCV image array
            
        Returns:
            Processed image array
        """
        try:
            # Convert to RGBA
            image_rgba = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
            
            # Remove background
            output = rembg.remove(image_rgba)
            
            return output
            
        except Exception as e:
            logger.error(f"Background removal failed: {e}")
            return image
    
    def _correct_colors(self, image: Image.Image) -> Image.Image:
        """Correct colors in image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Processed PIL Image object
        """
        try:
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # Enhance brightness
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
            
            # Enhance saturation
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.1)
            
            return image
            
        except Exception as e:
            logger.error(f"Color correction failed: {e}")
            return image
    
    def _correct_colors_cv2(self, image: np.ndarray) -> np.ndarray:
        """Correct colors in image using OpenCV.
        
        Args:
            image: OpenCV image array
            
        Returns:
            Processed image array
        """
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            
            # Split channels
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            
            # Merge channels
            lab = cv2.merge((l,a,b))
            
            # Convert back to BGR
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
        except Exception as e:
            logger.error(f"Color correction failed: {e}")
            return image
    
    def _add_watermark(self, image: Image.Image) -> Image.Image:
        """Add watermark to image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Processed PIL Image object
        """
        try:
            # Create watermark text
            watermark = Image.new('RGBA', image.size, (0,0,0,0))
            draw = ImageDraw.Draw(watermark)
            
            # Use a default font
            font = ImageFont.load_default()
            
            # Add text
            text = "Auction Intelligence"
            textwidth, textheight = draw.textsize(text, font)
            
            # Position in bottom right
            x = image.size[0] - textwidth - 10
            y = image.size[1] - textheight - 10
            
            # Draw text
            draw.text((x, y), text, font=font, fill=(255,255,255,128))
            
            # Composite images
            return Image.alpha_composite(image.convert('RGBA'), watermark)
            
        except Exception as e:
            logger.error(f"Watermark addition failed: {e}")
            return image
    
    def _generate_spin_frames(self, image: np.ndarray) -> List[np.ndarray]:
        """Generate 360° spin frames.
        
        Args:
            image: OpenCV image array
            
        Returns:
            List of frame arrays
        """
        try:
            frames = []
            
            # Get image center
            height, width = image.shape[:2]
            center = (width/2, height/2)
            
            # Generate rotation matrix
            for angle in range(0, 360, 5):
                matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                
                # Apply rotation
                rotated = cv2.warpAffine(
                    image,
                    matrix,
                    (width, height),
                    borderMode=cv2.BORDER_TRANSPARENT
                )
                
                frames.append(rotated)
            
            return frames
            
        except Exception as e:
            logger.error(f"Frame generation failed: {e}")
            return [] 