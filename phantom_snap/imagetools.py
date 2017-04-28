import os, base64


def save_image(filename, render_response):
    """
    Saves the rendered image to a file.
    
    :param filename: The full path and filename (without extension)
    :param render_response: The response object from the renderer
    :return: True if the file was written, False otherwise
    """
    if render_response is not None and \
       u'base64' in render_response and \
       render_response[u'base64'] is not None:

        image_base64 = render_response[u'base64']
        image_bytes = base64.decodestring(image_base64)

        image_format = render_response[u'format']

        file_path = u'{file}.{format}'.format(file=filename,
                                              format=image_format.lower())

        directory, filename = os.path.split(file_path)

        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, 'w') as file_stream:
            file_stream.write(image_bytes)

        return True

    return False
