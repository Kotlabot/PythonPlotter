# PythonPlotter
Software PythonPlotter slouží k přečtení hodnot z vybraného vstupu a vynesení hodnot do grafu.
Vstupem programu mohou být textové soubory s hodnotami, nebo vybraný sériový port. 

O práci se sériovými porty se stará port_reader.py. 
V nastavení programu je také možnost vybrat port "test", který generuje náhodné hodnoty a slouží
jako simulace existujícího USB portu.

Hodnoty v textových souberech jsou uloženy ve formátu:# Plot:<plotnumber 0-2>;X:<xIntVal>;Y:<yIntVal>;Z:<zIntVal>
Každá z jednotlivých hodnot X,Y,Z představuje jeden z bodů křivek x,y,z.

Program dále umožňuje upravovat viditelnost jednotlivých křivek v grafech pod menu View.
Pod menu Settings lze nalézt nastavení cesty pro uložení či načtení souboru, zvolení či
nalezení portu a pro nastavení maximálního počtu bodů aktuálně zobrazených v grafu pro každou křivku.

# Upozornění
Program je aktuálně určen pro užití na Linuxových systémech. Na využití pro Windows se stále pracuje.
Pro spuštění programu je nutné nainstalovat balíčky: matplotlib, pyudev, pySerial
