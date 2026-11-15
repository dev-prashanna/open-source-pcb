import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from assemble import assemble
class AssemblerTests(unittest.TestCase):
 def test_encoding(self):
  self.assertEqual(assemble('.equ LED 0x40\nstart: LDI 9\nOUT LED\nJMP start\nHLT'),[0x1009,0xe040,0xa000,1])
 def test_forward(self): self.assertEqual(assemble('JNZ end\nNOP\nend: HLT'),[0xf002,0,1])
 def test_errors(self):
  for s in ['LDI 256','JMP 4096','IN -1','ADD 1','BOGUS','x: NOP\nx: HLT','JMP missing','NOP\n'*4097]:
   with self.subTest(s=s[:30]),self.assertRaises(ValueError): assemble(s)
 def test_examples(self):
  for p in (Path(__file__).resolve().parents[1]/'examples').glob('*.asm'):
   self.assertTrue(assemble(p.read_text()))
if __name__=='__main__': unittest.main()
