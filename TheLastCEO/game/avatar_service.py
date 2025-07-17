import os
import logging
from typing import Optional, Tuple
from io import BytesIO
from PIL import Image
from google.cloud import storage
from django.conf import settings
import base64
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

logger = logging.getLogger(__name__)

class AvatarGenerationService:
    """Service for generating avatars using Google Cloud Imagen 4"""
    
    def __init__(self):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GOOGLE_APPLICATION_CREDENTIALS
        vertexai.init(
            project=settings.GOOGLE_CLOUD_PROJECT_ID,
            location='us-central1'
        )
        self.storage_client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT_ID)
        self.bucket = self.storage_client.bucket(settings.GOOGLE_CLOUD_BUCKET_NAME)
    
    def generate_avatar_prompt(self, headwear: str, accessory: str, gender: str, favorite_color: str) -> str:
        """Generate the prompt for avatar creation"""
        gender_description = "male" if gender == "male" else "female"
        return (
            f"A pixel art style square avatar head, only the head, centered and filling the entire 32x32px image, "
            f"with a {favorite_color} background color, no body, no shoulders, no other background elements. "
            f"The head should be fullscreen and fill the canvas. "
            f"Create a {gender_description} character wearing a {headwear} and {accessory}."
        )
    
    def generate_avatar_image(self, prompt: str) -> Optional[bytes]:
        """Generate avatar image using Google Cloud Imagen 4"""
        try:
            model = ImageGenerationModel.from_pretrained("imagen-4.0-generate-preview-06-06")
            response = model.generate_images(
                prompt=prompt,
                number_of_images=1
            )
            images = getattr(response, 'images', None)
            if not images or len(images) == 0:
                logger.error("No image generated from Imagen API (empty response)")
                return None
            img_obj = images[0]
            pil_img = None
            # Try _image_bytes
            if hasattr(img_obj, '_image_bytes') and img_obj._image_bytes:
                pil_img = Image.open(BytesIO(img_obj._image_bytes))
            # Try _pil_image
            elif hasattr(img_obj, '_pil_image') and img_obj._pil_image:
                pil_img = img_obj._pil_image
            # Try _as_base64_string
            elif hasattr(img_obj, '_as_base64_string') and img_obj._as_base64_string():
                try:
                    img_bytes = base64.b64decode(img_obj._as_base64_string())
                    pil_img = Image.open(BytesIO(img_bytes))
                except Exception as e:
                    logger.error(f"Failed to decode base64 image: {str(e)}")
                    return None
            if pil_img is None:
                logger.error("No usable image data found in Imagen API response.")
                return None
            pil_img = pil_img.convert('RGBA') if pil_img.mode != 'RGBA' else pil_img
            pil_img = pil_img.resize((32, 32), Image.Resampling.LANCZOS)
            output = BytesIO()
            pil_img.save(output, format='PNG', optimize=True)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Error generating avatar image: {str(e)}")
            return None
    
    def upload_to_cloud_storage(self, image_bytes: bytes, user_id: int) -> Optional[str]:
        """Upload avatar image to Google Cloud Storage"""
        try:
            blob_path = f"avatars/{user_id}.png"
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(
                image_bytes,
                content_type='image/png'
            )
            # Do not call blob.make_public()! Uniform bucket-level access is enabled.
            # To make the file public, set bucket permissions via IAM in the GCP Console.
            return f"https://storage.googleapis.com/{self.bucket.name}/{blob.name}"
        except Exception as e:
            logger.error(f"Error uploading avatar to Cloud Storage: {str(e)}")
            return None
    
    def generate_and_upload_avatar(self, user_id: int, headwear: str, accessory: str, gender: str, favorite_color: str) -> Tuple[bool, Optional[str]]:
        try:
            prompt = self.generate_avatar_prompt(headwear, accessory, gender, favorite_color)
            logger.info(f"Generating avatar for user {user_id} with prompt: {prompt}")
            image_bytes = self.generate_avatar_image(prompt)
            if not image_bytes:
                return False, None
            avatar_url = self.upload_to_cloud_storage(image_bytes, user_id)
            if not avatar_url:
                return False, None
            logger.info(f"Avatar generated successfully for user {user_id}: {avatar_url}")
            return True, avatar_url
        except Exception as e:
            logger.error(f"Error in avatar generation process: {str(e)}")
            return False, None

# Singleton instance
avatar_service = AvatarGenerationService() 