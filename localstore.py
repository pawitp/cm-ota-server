import logging


def get_file(filename):
    try:
        # Use basketbuild for all URLs
        return "https://s.basketbuild.com/uploads/devs/pawitp/i9082_cm12.0/" + filename
    except Exception, e:
        logging.error("Unable to query CDN " + str(e))
        return None
