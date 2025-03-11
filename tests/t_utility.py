import os

ROOT_DIR = os.getcwd()


def get_working_directory_test():
    if ROOT_DIR.endswith('tests') or ROOT_DIR.endswith('tests/'):
        return ROOT_DIR
    else:
        return os.path.join(ROOT_DIR, 'tests')

def get_test_resources_folder():
    return os.path.join(get_working_directory_test(), 'resources')