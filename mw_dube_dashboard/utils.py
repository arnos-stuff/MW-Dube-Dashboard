from pathlib import Path

__all__ = ['src', 'pkg', 'data', 'csvFiles', 'csvMap', 'preprocData', 'csvPreprocessed']

src = Path(__file__).parent
pkg = src.parent
data = src / 'data'
preprocData = data / 'processed'


# files

csvFiles = list(data.glob('*.csv'))
csvMap = {f.stem: f for f in csvFiles}
csvPreprocessed = next(preprocData.glob('*.csv'), [])