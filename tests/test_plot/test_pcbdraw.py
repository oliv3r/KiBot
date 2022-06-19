"""
Tests for PcbDraw.

For debug information use:
pytest-3 --log-cli-level debug
"""
import coverage
import logging
from shutil import which
from os import access
from importlib import reload
from . import context
from kibot.mcpyrate import activate  # noqa: F401
from kibot.out_pcbdraw import PcbDrawOptions
import kibot.log

OUT_DIR = 'PcbDraw'
cov = coverage.Coverage()


def test_pcbdraw_3Rs(test_dir):
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'pcbdraw', OUT_DIR)
    ctx.run()
    ctx.expect_out_file_d(prj+'-top.svg')
    ctx.expect_out_file_d(prj+'-bottom.svg')
    ctx.clean_up()


def test_pcbdraw_simple(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'pcbdraw_simple', OUT_DIR)
    ctx.run()
    ctx.expect_out_file_d(prj+'-top.png')
    ctx.expect_out_file_d(prj+'-bottom.jpg')
    ctx.clean_up()


def no_rsvg_convert(name):
    logging.debug('no_rsvg_convert called')
    if name == 'rsvg-convert':
        logging.debug('no_rsvg_convert returns None')
        return None
    return which(name)


def no_rsvg_convert_access(name, attrs):
    logging.debug('no_rsvg_convert_access')
    if name.endswith('/rsvg-convert'):
        logging.debug('no_rsvg_convert_access returns False')
        return False
    return access(name, attrs)


def no_convert(name):
    logging.debug('no_convert called')
    if name == 'convert':
        logging.debug('no_convert returns None')
        return None
    return which(name)


def no_convert_access(name, attrs):
    logging.debug('no_convert_access')
    if name.endswith('/convert'):
        logging.debug('no_convert_access returns False')
        return False
    return access(name, attrs)


def no_run(cmd, stderr, text=False):
    return b""


def platform_system_bogus():
    return 'Bogus'


def test_pcbdraw_miss_rsvg(caplog, monkeypatch):
    """ Check missing rsvg-convert """
    with monkeypatch.context() as m:
        # Make which('rsvg-convert') fail
        m.setattr("shutil.which", no_rsvg_convert)
        # Make the call to determine the version fail
        m.setattr("subprocess.check_output", no_run)
        # Make os.access(...rsvg-convert', EXEC) fail
        m.setattr("os.access", no_rsvg_convert_access)
        # Make platform.system() return a bogus OS
        m.setattr("platform.system", platform_system_bogus)
        # Reload the module so we get the above patches
        reload(kibot.dep_downloader)
        old_lev = kibot.log.debug_level
        kibot.log.debug_level = 2
        o = PcbDrawOptions()
        o.style = ''
        o.remap = None
        o.format = 'jpg'
        o.config(None)
        cov.load()
        cov.start()
        o.run('')
        cov.stop()
        cov.save()
        kibot.log.debug_level = old_lev
        assert 'using unreliable PNG/JPG' in caplog.text, caplog.text
        assert 'librsvg2-bin' in caplog.text, caplog.text


def test_pcbdraw_miss_convert(caplog, monkeypatch):
    """ Check missing convert """
    with monkeypatch.context() as m:
        m.setattr("shutil.which", no_convert)
        m.setattr("subprocess.check_output", no_run)
        m.setattr("os.access", no_convert_access)
        # Make platform.system() return a bogus OS
        m.setattr("platform.system", platform_system_bogus)
        # Reload the module so we get the above patches
        reload(kibot.dep_downloader)
        o = PcbDrawOptions()
        o.style = ''
        o.remap = None
        o.format = 'jpg'
        o.config(None)
        cov.load()
        cov.start()
        o.run('')
        cov.stop()
        cov.save()
        assert 'using unreliable PNG/JPG' in caplog.text, caplog.text
        assert 'imagemagick' in caplog.text, caplog.text


def test_pcbdraw_variant_1(test_dir):
    prj = 'kibom-variant_3'
    ctx = context.TestContext(test_dir, prj, 'pcbdraw_variant_1', '')
    ctx.run()
    # Check all outputs are there
    fname = prj+'-top.png'
    ctx.expect_out_file(fname)
    # We use 40% because different versions of the tools are generating large differences
    # in the borders. With 40% these differences are removed and we still detect is a
    # components was removed.
    # Expected: R1 and R2 populated
    ctx.compare_image(fname, fuzz='40%')
    ctx.clean_up(keep_project=True)


def test_pcbdraw_variant_2(test_dir):
    prj = 'kibom-variant_3'
    ctx = context.TestContext(test_dir, prj, 'pcbdraw_variant_2', '')
    ctx.run()
    # Check all outputs are there
    fname = prj+'-top-C1.png'
    ctx.expect_out_file(fname)
    # Expected: R1 and R2 populated + C1 manually added
    ctx.compare_image(fname, fuzz='40%')
    ctx.clean_up(keep_project=True)


def test_pcbdraw_variant_3(test_dir):
    prj = 'kibom-variant_3'
    ctx = context.TestContext(test_dir, prj, 'pcbdraw_variant_3', '')
    ctx.run()
    # Check all outputs are there
    fname = prj+'-top.png'
    ctx.expect_out_file(fname)
    ctx.compare_image(fname, fuzz='40%')
    assert ctx.search_err("Ambiguous list of components to show .?none.? vs variant/filter")
    ctx.clean_up(keep_project=True)
