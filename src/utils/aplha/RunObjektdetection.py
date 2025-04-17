from src.utils.aplha.treeMatrix import TreeMatrix

matrix = TreeMatrix("pfad/zu/objekte_D.txt")
alle_objekte = matrix.get_alle_objekte()

# Beispiel: Vertrauenswürdige Punkte ausgeben
vertrauenswuerdige_punkte = [obj for obj in matrix.get_objekte_nach_klasse("point")
                             if obj.ist_vertrauenswuerdig(70.0)]
for punkt in vertrauenswuerdige_punkte:
    print(punkt)