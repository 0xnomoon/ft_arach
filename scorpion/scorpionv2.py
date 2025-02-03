import argparse
import os
import pathlib
from PIL import Image, ExifTags

# Function to extract basic file information
def extract_basic_file_info(image_path, metadata):
    metadata['Filename'] = os.path.basename(image_path)
    metadata['Directory'] = os.path.dirname(image_path.resolve())
    metadata['File Size'] = os.path.getsize(image_path)
    metadata['Creation Date'] = os.path.getctime(image_path)
    metadata['Modification Date'] = os.path.getmtime(image_path)

# Function to extract basic image information
def extract_basic_image_info(image, metadata):
    metadata['Format'] = image.format
    metadata['Mode'] = image.mode
    metadata['Image Width'] = image.width
    metadata['Image Height'] = image.height

# Function to extract EXIF data
def extract_image_exif(image, metadata):
    exifdata = image.getexif()
    for tag_id, value in exifdata.items():
        tag = ExifTags.TAGS.get(tag_id, tag_id)
        metadata[tag] = value

# Function to display image metadata
def display_image_metadata(args, image_path, index):
    print(f"Image {index}/{len(args.image)}: {image_path}")
    metadata = {}
    try:
        extract_basic_file_info(image_path, metadata)
        with Image.open(image_path) as image:
            extract_basic_image_info(image, metadata)
            extract_image_exif(image, metadata)
        for key, value in metadata.items():
            print(f"{key}: {value}")
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

# Function to strip metadata from an image
def strip_image_metadata(args, image_path, index):
    stripped_file_name = f"{os.path.splitext(image_path)[0]}_stripped{os.path.splitext(image_path)[1]}"
    try:
        with Image.open(image_path) as original:
            stripped = Image.new(original.mode, original.size)
            stripped.putdata(list(original.getdata()))
            stripped.save(stripped_file_name)
            print(f"Stripped metadata from {image_path} and saved as {stripped_file_name}")
    except Exception as e:
        print(f"Error stripping metadata from {image_path}: {e}")

# Main processing function
def process_metadata(args):
    if args.delete:
        print("Deleting metadata...")
    for i, image in enumerate(args.image):
        if args.delete:
            strip_image_metadata(args, image, i + 1)
        else:
            display_image_metadata(args, image, i + 1)

# Argument parsing
def parse_args():
    parser = argparse.ArgumentParser(description="An image metadata viewer")
    parser.add_argument('image', type=pathlib.Path, nargs='+', help="Images to view or modify EXIF data for.")
    parser.add_argument('-d', '--delete', action='store_true', help="Delete all EXIF data from images.")
    return parser.parse_args()

# Main function
def main():
    args = parse_args()
    process_metadata(args)

if __name__ == '__main__':
    main()
