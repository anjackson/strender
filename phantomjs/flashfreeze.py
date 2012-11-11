from ghost import Ghost
import sys

def main(argv):
    if len(argv) < 2:
        sys.stderr.write("Usage: %s <url>\n" % (argv[0],))
        return 1

    ghost = Ghost(viewport_size=(1280, 1024))
    page, resources = ghost.open(argv[1])
    assert page.http_status==200 and 'bbc' in ghost.content
    ghost.capture_to('screenshot2.png')

    for r in resources:
      print r.url

if __name__ == "__main__":
    sys.exit(main(sys.argv))
