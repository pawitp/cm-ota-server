import logging


def get_file(filename, rom):
    try:
        # Use basketbuild for all URLs
        if rom == "cm-12":
            return "https://s.basketbuild.com/uploads/devs/pawitp/i9082_cm12.0/" + filename
        elif rom == "cm-12-1":
            return "https://s.basketbuild.com/uploads/devs/pawitp/i9082_cm12.1/" + filename
        else:
            raise Exception("Unknown rom")
    except Exception, e:
        logging.error("Unable to query CDN " + str(e))
        return None
