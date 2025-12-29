# Automatically download and update this collection of snippets to your local snippet folder

from zipfile import ZipFile
from tempfile import TemporaryFile
import os

domain = b'https://gist.github.com'
path = b'/psifertex/6fbc7532f536775194edd26290892ef7' # Feel free to adapt to your own setup
subfolder = 'default'                                 # Change to save the snippets to a different sub-folder
tab2space = False
width = 4

def download(url):
    # Can also use 'CoreDownloadProvider' or 'PythonDownloadProvider' as keys here
    provider = DownloadProvider[Settings().get_string('network.downloadProviderName')].create_instance()
    code, data = provider.get_response(url)
    if code == 0:
        return data
    else:
        raise ConnectionError("Unsuccessful download of %s" % url)

def update_snippets():
    if not interaction.show_message_box('Warning', "Use at your own risk. Do you want to automatically overwrite local snippets from gist?", buttons=MessageBoxButtonSet.YesNoButtonSet):
        return
    snippetPath = os.path.realpath(os.path.join(user_plugin_path(), '..', 'snippets', subfolder))
    if not os.path.isdir(snippetPath):
        os.makedirs(snippetPath)
    url = domain + path
    log_info("Downloading from: %s" % url)
    source = download(url)
    zipPath = [s for s in source.split(b'\"') if s.endswith(b'.zip') and b'/archive/' in s]
    if len(zipPath) == 0:
        log_error("Update failed: No archive ZIP found.")
        return
    # Take the first match (there may be duplicates)
    url = domain + zipPath[0]

    log_info("Downloading from: %s" % url)
    zip = download(url)
    with TemporaryFile() as f:
        f.write(zip)
        with ZipFile(f, 'r') as zip:
            for item in zip.infolist():
                if item.filename[-1] == '/':
                    continue
                basename = os.path.basename(item.filename)
                targetPath = os.path.join(snippetPath, basename)

                # Read remote content
                remote_content = zip.read(item)
                if tab2space:
                    remote_content = remote_content.replace(b'\t', b' ' * width)

                # Merge with local if file exists (preserve first two lines)
                if os.path.exists(targetPath):
                    with open(targetPath, 'rb') as local_file:
                        local_lines = local_file.readlines()

                    # If local file has at least 2 lines, preserve them
                    if len(local_lines) >= 2:
                        remote_lines = remote_content.splitlines(keepends=True)
                        if len(remote_lines) >= 2:
                            # Keep first two lines from local, rest from remote
                            merged_content = b''.join(local_lines[:2] + remote_lines[2:])
                            log_info("Merging %s (preserving local description/hotkey)" % item.filename)
                        else:
                            # Remote file too short, just use it as-is
                            merged_content = remote_content
                    else:
                        # Local file too short, just use remote
                        merged_content = remote_content
                else:
                    merged_content = remote_content

                with open(targetPath, 'wb') as f:
                    f.write(merged_content)
                    log_info("Extracting %s" % item.filename)

update_snippets()
