# importer toutes les librairies
import matplotlib.pyplot as plt
import parselmouth
import textgrids
from parselmouth.praat import call

#fonction pour ouvrir notre dictionnaire
def ouvrir_dico(fichier):
    dico = {}
    with open(fichier, "r", encoding="utf-8") as fichier: #on ouvre le dictionnaire en le lisant et on spécifie qu'il s'agit d'un UTF-8
        for ligne in fichier:
            cle, valeur = ligne.strip().split("\t") #dinstinction entre clé et valeur en les séparant
            dico[cle] = valeur
    return dico

#fonction pour avoir la représentation phonétiques de nos phrases/mots
def phonetisation(phrase, dico):
    mots = phrase.split()
    phrase_phonetique = [] 
    
    for mot in mots:
        prononciation = dico.get(mot, "") #avec .get() on récupère la prononciation dans le dictionnaire
        phrase_phonetique.append(prononciation) #ajout la prononciation à la liste
        
    return "".join(phrase_phonetique)

#fonction pour modifier la fréquence fondamentale de notre fichier son
def modification_f0(extrait, son):
    allongement = 1
    
    #manipulation du son
    manip = call(extrait, "To Manipulation", 0.01, 75, 600)
    duration_tier = call(manip, "Extract duration tier")

    pitch_tier = call(manip, "Extract pitch tier")
    nb_f0_pitch = call(pitch_tier, "Get number of points")
    
    if nb_f0_pitch > 0:
        call(pitch_tier, "Remove points between", 0, extrait.duration)
        call(pitch_tier, "Add point", 0.01, 215) #on décide de mettre 210 Hz pour notre synthèse
        call([manip, pitch_tier], "Replace pitch tier")
        extrait = call(manip, "Get resynthesis (overlap-add)")
        
    call(duration_tier, "Remove points between", 0, extrait.duration)
    call(duration_tier, "Add point", extrait.duration / 2, allongement)
    call([manip, duration_tier], "Replace duration tier")

    return call(manip, "Get resynthesis (overlap-add)")

# fonction matplotlib pour visualiser notre son/synthèse
def visualisation(son):
    plt.figure()
    plt.plot(son.xs(), son.values.T)
    plt.xlabel("Temps")
    plt.ylabel("Amplitude")
    plt.title("Son Final")
    plt.show()

# fonction pour lire notre fichier texte de nos phrase
def lire_phrases(fichier):
    with open(fichier, "r", encoding="utf-8") as fichier: #lire le fichier texte de nos phrases
        phrases = fichier.readlines() #lire toutes les lignes
    return phrases

#fonction du traitement de nos phrases
def traitement(phrases, dictionnaire, son, grille, synthese):
    son = parselmouth.Sound(son)
    debut = son.extract_part(0, 0.01, parselmouth.WindowShape.RECTANGULAR, 1, False)
    
    #on parcourt chaque phrase
    for phrase in phrases:
        phrase_phonetique = "_" + phonetisation(phrase, dictionnaire) + "_" #ajout du son initial et final pour chaque phrase
        print(phrase_phonetique) #on va printer nos phrases

        segmentation = textgrids.TextGrid(grille)
        diphones = segmentation["phonemes"]
        verbe = ["aime", "sentez", "est", "sent", "trouve", "aime", "aiment"] #liste de verbe

        for i in range(len(phrase_phonetique) - 1):
            phoneme1 = phrase_phonetique[i]
            phoneme2 = phrase_phonetique[i + 1]
            
            # allongement de la durée de nos diphones si le script tombe sur un verbe de notre liste
            if phoneme1 == "verbe" and phoneme2 == "verbe":
                allongement = 2
            else:
                allongement = 1
            
            # parcourir nos diphones : trouver le milieu 1 et 2 + la concaténation
            for a in range(len(diphones) - 1):
                b = a + 1
                if diphones[a].text == phoneme1 and diphones[b].text == phoneme2:
                    milieu_phoneme1 = diphones[a].xmin + (diphones[a].xmax - diphones[a].xmin) / 2
                    milieu_phoneme1 = son.get_nearest_zero_crossing(milieu_phoneme1, 1)

                    milieu_phoneme2 = diphones[b].xmin + (diphones[b].xmax - diphones[b].xmin) / 2
                    milieu_phoneme2 = son.get_nearest_zero_crossing(milieu_phoneme2, 1)

                    extrait = son.extract_part(milieu_phoneme1, milieu_phoneme2, parselmouth.WindowShape.RECTANGULAR, 1, False)
                    extrait_manipule = modification_f0(extrait, son)
                    debut = debut.concatenate([debut, extrait_manipule])
                    break

        debut = debut.concatenate([debut, son.extract_part(debut.get_total_duration() - 0.01, debut.get_total_duration(), parselmouth.WindowShape.RECTANGULAR, 1, False)])

    debut.save(synthese, parselmouth.SoundFileFormat.WAV)
    visualisation(debut) #affiche la visualisation matplotlib / représentation de notre fichier son

if __name__ == "__main__": # notre main
    son = "patricia.wav"
    grille = "patricia.TextGrid"
    synthese = "synthese.wav" # notre fichier son qui va se créer après le lancement du script : vous pouvez modifier l'intitulé
    dictionnaire = "dico_UTF8.txt"
    phrases = "phrases.txt" # notre fichier texte avec toutes nos phrases (1 ligne = 1 phrase)
    
    #appel la fonction traitement() avec nos fonctions/fichiers
    traitement(lire_phrases(phrases), ouvrir_dico(dictionnaire), son, grille, synthese)
