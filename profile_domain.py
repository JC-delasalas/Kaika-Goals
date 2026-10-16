"""Kaika-owned profile settings. Workday remains the identity source."""
import base64,io,warnings
from PIL import Image,ImageOps,UnidentifiedImageError
from demo_mutations import require,Invalid

def normalize_profile(actor,payload):
 require(payload.get('person_id',actor)==actor,'You can only customize your own profile.',403)
 style=payload.get('avatar_style',0)
 require(type(style) is int and 0<=style<6,'Choose one of the available avatars.')
 revision=payload.get('expected_revision',0)
 require(type(revision) is int and revision>=0,'Invalid profile revision.')
 result={'person_id':actor,'avatar_style':style,'expected_revision':revision,'photo_data_url':None}
 photo=payload.get('photo_data_url')
 if not photo:return result
 require(isinstance(photo,str) and len(photo)<=700000,'Profile image is too large.')
 try:
  header,encoded=photo.split(',',1)
  require(header in ('data:image/jpeg;base64','data:image/png;base64','data:image/webp;base64'),'Use a JPEG, PNG or WebP image.')
  raw=base64.b64decode(encoded,validate=True)
  with warnings.catch_warnings():
   warnings.simplefilter('error',Image.DecompressionBombWarning)
   with Image.open(io.BytesIO(raw)) as im:
    require(im.format in ('JPEG','PNG','WEBP') and im.width*im.height<=16000000,'Use a still image under 16 megapixels.')
    require(getattr(im,'n_frames',1)==1,'Use a still image, not an animation.')
    im.load();im=ImageOps.exif_transpose(im)
    im=ImageOps.fit(im.convert('RGB'),(160,160),method=Image.Resampling.LANCZOS)
    im.info.clear()
    out=io.BytesIO();im.save(out,format='JPEG',quality=82,optimize=True)
  require(len(out.getvalue())<=32000,'Image could not be reduced safely. Try a simpler image.')
  result['photo_data_url']='data:image/jpeg;base64,'+base64.b64encode(out.getvalue()).decode()
 except (ValueError,OSError,UnidentifiedImageError,Image.DecompressionBombWarning,Image.DecompressionBombError) as e:
  raise Invalid('The file is not a valid supported image.') from e
 return result
