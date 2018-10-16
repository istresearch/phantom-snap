SCHEMA = {
    "1.0": {
        "render": {
            "properties": {
                "url": {
                    "type": "string",
                    "minLength": 3
                },
                "html": {
                    # default is None
                    "type": "string",
                    "minLength": 1,
                    "binaryEncoding": "base64",
                    "contentMediaType": "text/html"
                },
                "img_format": {
                    # default here is PNG
                    "type": "string",
                    "enum": [
                        "PDF",
                        "PNG",
                        "JPEG",
                        "BMP",
                        "PPM",
                    ]
                },
                "width": {
                    # default 1280
                    "type": "number",
                    "minimum": 1
                },
                "height": {
                    # default 1024
                    "type": "number",
                    "minimum": 1
                },
                "page_load_timeout": {
                    # default None
                    "type": "number",
                    "minimum": 1
                },
                "user_agent": {
                    # default None
                    "type": "string",
                    "minLength": 1
                },
                "headers": {
                    # default None
                    "type": "object"
                },
                "cookies": {
                    # default None
                    "type": "object"
                },
                "html_encoding": {
                    # default utf-8
                    "type": "string",
                    "minLength": 1
                },
            },
            "required": [
                "url"
            ],
            "additionalProperties": False
        }
    }
}