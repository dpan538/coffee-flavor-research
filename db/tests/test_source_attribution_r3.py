import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import source_attribution_r3 as a


class AttributionTests(unittest.TestCase):
    def test_group_roles_do_not_turn_editor_into_author(self):
        root = ET.fromstring('''<article><article-meta><article-title>Synthetic title</article-title><article-id pub-id-type="doi">10.0000/synthetic</article-id><contrib-group content-type="author"><contrib><name><surname>A</surname><given-names>Ada</given-names></name></contrib></contrib-group><contrib-group content-type="editor"><contrib><name><surname>B</surname><given-names>Bo</given-names></name></contrib></contrib-group><pub-date><day>9</day><month>2</month><year>2025</year></pub-date></article-meta></article>''')
        result = a.attribution(root)
        self.assertEqual(result["authors"], ["Ada A"])
        self.assertEqual(result["editors_not_authors"], ["Bo B"])
        self.assertEqual(result["publication_dates"][0]["iso_date"], "2025-02-09")

    def test_missing_author_information_is_not_silently_admitted(self):
        with self.assertRaisesRegex(ValueError, "AUTHOR_GROUP"):
            a.attribution(ET.fromstring("<article><article-meta/></article>"))


if __name__ == "__main__":
    unittest.main()
