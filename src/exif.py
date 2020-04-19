import PIL.Image
img = PIL.Image.open('out/gmi_ulA42_376371_O-71_187576_lRA42_369949_O-71_181274_640x640_sc1z19_h_mr45_AUG.png')
exif_data = img._getexif()
# This should give you a dictionary indexed by EXIF numeric tags.
# If you want the dictionary indexed by the actual EXIF tag name strings, try something like:

import PIL.ExifTags
exif = {
    PIL.ExifTags.TAGS[k]: v
    for k, v in img._getexif().items()
    if k in PIL.ExifTags.TAGS
}