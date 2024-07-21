def s3_object_key_generator(ext,*args):
    key = ""
    length = len(args)
    for i, arg in enumerate(args):
        if(i < length-1):
            key += f"{arg}/"
        else:
            key += f"{arg}"
    
    key += f".{ext}"

    return key
