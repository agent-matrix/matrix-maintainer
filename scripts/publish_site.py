from matrix_maintainer.site.generator import generate_site
from matrix_maintainer.settings import get_settings

if __name__ == "__main__":
    generate_site(get_settings())
