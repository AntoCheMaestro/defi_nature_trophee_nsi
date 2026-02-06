import pygame
import sys
import random
import numpy as np

pygame.init()

# ============================================================
# ======================= CERVEAU DU JEU ======================
# ============================================================

class Animaux:
    def __init__(self, nom, poids, longueur, longevite):
        self.nom = nom
        self.poids = poids
        self.longueur = longueur
        self.longevite = longevite

    def __repr__(self):
        return f"{self.nom} | Poids:{self.poids} Longueur:{self.longueur} Longévité:{self.longevite}"


class Joueur:
    def __init__(self, nom, cartes):
        self.nom = nom
        self.cartes = cartes

    def carte_visible(self):
        return self.cartes[-1]

    def enlever_carte(self):
        return self.cartes.pop()

    def ajouter_carte(self, carte):
        # réinsertion aléatoire (comme ton code)
        self.cartes.insert(random.randint(0, len(self.cartes)), carte)

    def est_vaincu(self):
        return len(self.cartes) == 0


def distribuer_cartes(liste):
    cartes = liste.copy()
    random.shuffle(cartes)
    milieu = len(cartes) // 2
    return cartes[:milieu], cartes[milieu:]


def choix_robot_aleatoire():
    return random.choice(["poids", "longueur", "longevite"])


def choix_robot_intelligent(carte, historique):
    # version médiane (comme ton code)
    if not historique:
        return choix_robot_aleatoire()

    poids_m = np.median([c.poids for c in historique])
    longueur_m = np.median([c.longueur for c in historique])
    longevite_m = np.median([c.longevite for c in historique])

    scores = {
        "poids": carte.poids / poids_m if poids_m > 0 else 0,
        "longueur": carte.longueur / longueur_m if longueur_m > 0 else 0,
        "longevite": carte.longevite / longevite_m if longevite_m > 0 else 0
    }
    return max(scores, key=scores.get)


class GameState:
    """
    GameState = moteur prêt pour interface (Pygame)
    - aucune UI ici
    - invariants inclus
    """
    def __init__(self, joueur1, joueur2, mode_robot=None):
        self.joueurs = [joueur1, joueur2]
        self.joueur_actif = joueur1
        self.joueur_passif = joueur2

        # mode_robot : None (PvP), "A" (aléatoire), "I" (intelligent)
        self.mode_robot = mode_robot

        self.historique_cartes = []
        self.cartes_initiales = joueur1.cartes + joueur2.cartes

        self.terminee = False
        self.gagnant = None

        # infos de dernière manche pour affichage
        self.derniere_carac = None
        self.derniere_val_actif = None
        self.derniere_val_passif = None
        self.dernier_gagnant = None

    def actif_est_robot(self):
        if self.mode_robot is None:
            return False
        return self.joueur_actif.nom.lower() == "robot"

    def appliquer_manche(self, caracteristique):
        """
        caracteristique: 'poids' / 'longueur' / 'longevite'
        Règle conservée: si égalité -> joueur actif PERD (car v_actif > v_passif strict)
        """
        if self.terminee:
            return

        carte_active = self.joueur_actif.carte_visible()
        carte_adverse = self.joueur_passif.carte_visible()

        v1 = getattr(carte_active, caracteristique)
        v2 = getattr(carte_adverse, caracteristique)

        # strict >
        if v1 > v2:
            gagnant, perdant = self.joueur_actif, self.joueur_passif
        else:
            gagnant, perdant = self.joueur_passif, self.joueur_actif

        # transfert + réinsertion aléatoire (comme ton moteur)
        carte_perdue = perdant.enlever_carte()
        gagnant.ajouter_carte(carte_perdue)

        carte_jouee = gagnant.enlever_carte()
        gagnant.ajouter_carte(carte_jouee)

        self.historique_cartes.extend([carte_active, carte_adverse])
        self._verifier_invariants()

        # stock infos pour UI
        self.derniere_carac = caracteristique
        self.derniere_val_actif = v1
        self.derniere_val_passif = v2
        self.dernier_gagnant = gagnant

        if perdant.est_vaincu():
            self.terminee = True
            self.gagnant = gagnant
            return

        # alternance
        self.joueur_actif, self.joueur_passif = self.joueur_passif, self.joueur_actif

    def _verifier_invariants(self):
        toutes = []
        for j in self.joueurs:
            toutes.extend(j.cartes)

        assert len(toutes) == len(self.cartes_initiales), "ERREUR: nombre total de cartes a changé"
        assert len(set(id(c) for c in toutes)) == len(toutes), "ERREUR: duplication de cartes détectée"
        assert set(id(c) for c in toutes) == set(id(c) for c in self.cartes_initiales), (
            "ERREUR: carte disparue ou carte inconnue apparue"
        )


LISTE_ANIMAUX = [
    Animaux("Lion", 190, 250, 14),
    Animaux("Éléphant", 6000, 600, 70),
    Animaux("Tigre", 220, 290, 16),
    Animaux("Girafe", 1200, 500, 25),
    Animaux("Rhinocéros", 2500, 400, 50),
    Animaux("Crocodile", 500, 520, 70),
    Animaux("Ours", 600, 280, 30),
    Animaux("Loup", 50, 160, 13),
    Animaux("Zèbre", 350, 250, 25),
    Animaux("Hippopotame", 1500, 350, 40),
    Animaux("Kangourou", 85, 230, 23),
    Animaux("Panthère", 90, 180, 15),
    Animaux("Chien", 40, 110, 13),
    Animaux("Chat", 5, 50, 15),
    Animaux("Aigle", 6, 220, 25),
    Animaux("Tortue", 300, 150, 100),
]


def creer_partie(mode, prenom="Humain"):
    """
    mode:
      "PVP" -> Joueur 1 vs Joueur 2
      "RA"  -> Humain vs Robot aléatoire
      "RI"  -> Humain vs Robot intelligent
    """
    c1, c2 = distribuer_cartes(LISTE_ANIMAUX)

    if mode == "PVP":
        j1 = Joueur("Joueur 1", c1)
        j2 = Joueur("Joueur 2", c2)
        return GameState(j1, j2, mode_robot=None)

    if mode == "RA":
        humain = Joueur(prenom if prenom.strip() else "Humain", c1)
        robot = Joueur("Robot", c2)
        return GameState(humain, robot, mode_robot="A")

    if mode == "RI":
        humain = Joueur(prenom if prenom.strip() else "Humain", c1)
        robot = Joueur("Robot", c2)
        return GameState(humain, robot, mode_robot="I")

    raise ValueError("Mode inconnu")


# ============================================================
# ======================= PYGAME / UI =========================
# ============================================================

# Fenêtre
LARGEUR, HAUTEUR = 700, 500
fenetre = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Défi Nature")

# Couleurs (ta maquette)
FOND = (30, 34, 40)
PANEL = (42, 47, 54)
VERT_NATURE = (58, 125, 90)
CARTE_COL = (230, 216, 181)
BOUTON = (220, 220, 220)
BOUTON_ACTIF = (242, 201, 76)
BLANC = (245, 245, 245)
NOIR = (26, 26, 26)

# Polices
police_titre = pygame.font.SysFont("arial", 36, bold=True)
police = pygame.font.SysFont("arial", 20)
police_menu = pygame.font.SysFont("arial", 28, bold=True)
police_petite = pygame.font.SysFont("arial", 16)

# Surfaces (ta maquette)
frame_haut = pygame.Surface((LARGEUR, 80))
frame_gauche = pygame.Surface((150, HAUTEUR - 80))
frame_jeu = pygame.Surface((LARGEUR - 150, HAUTEUR - 80))

frame_j1 = pygame.Surface(((frame_jeu.get_width() - 10) // 2, frame_jeu.get_height() - 90))
frame_j2 = pygame.Surface(((frame_jeu.get_width() - 10) // 2, frame_jeu.get_height() - 90))

# Menu hamburger (ta maquette)
menu_ouvert = False
options = ["Rejouer", "Règles", "Quitter"]
bouton_menu = pygame.Rect(20, 20, 40, 40)
option_rects = [pygame.Rect(20, 80 + i * 55, 110, 40) for i in range(len(options))]

# Zone carte (ta maquette)
zone_carte = pygame.Rect(20, 20, frame_j1.get_width() - 40, frame_j1.get_height() - 40)

# Boutons caractéristiques (ta maquette)
caracteristiques = [("Poids", "poids"), ("Longueur", "longueur"), ("Longévité", "longevite")]
boutons_carac = []
BTN_W, BTN_H = 140, 40
y_btn = frame_jeu.get_height() - 50
for i, (label, key) in enumerate(caracteristiques):
    x = 40 + i * (BTN_W + 20)
    boutons_carac.append((label, key, pygame.Rect(x, y_btn, BTN_W, BTN_H)))

# Bandeau "Tour de ..."
tour_bar_rect = pygame.Rect(20, frame_jeu.get_height() - 85, frame_jeu.get_width() - 40, 28)

# Règles (adaptées et affichées avec wrap automatique)
regles_texte = [
    "Modes : Joueur vs Joueur / Joueur vs Robot.",
    "Chaque carte représente un animal avec : Poids, Longueur, Longévité.",
    "Toutes les cartes sont mélangées puis distribuées équitablement entre les joueurs.",
    "Chaque joueur joue la dernière carte de son tas (carte visible).",
    "Le joueur actif choisit une caractéristique.",
    "La valeur la plus élevée remporte la manche.",
    "Règle importante : en cas d'égalité, le joueur actif perd la manche.",
    "Le gagnant récupère la carte adverse et sa carte jouée est réinsérée aléatoirement.",
    "La partie se termine lorsqu’un joueur n’a plus de cartes."
]
afficher_regles = False

# États UI (machine à états)
UI_START = "START"        # choix mode + prénom
UI_PLAY = "PLAY"          # choix carac / robot auto
UI_RESULT = "RESULT"      # résultat manche, clic pour continuer
UI_END = "END"            # fin de partie

ui_state = UI_START
game = None
message_ui = ""

# Start screen : boutons mode
start_buttons = [
    ("Joueur vs Joueur", "PVP", pygame.Rect(220, 220, 260, 52)),
    ("Vs Robot aléatoire", "RA", pygame.Rect(220, 285, 260, 52)),
    ("Vs Robot intelligent", "RI", pygame.Rect(220, 350, 260, 52)),
]

# Start screen : entrée prénom
prenom = ""
prenom_actif = True
input_rect = pygame.Rect(220, 155, 260, 45)

# Bouton "effacer"
clear_rect = pygame.Rect(490, 155, 40, 45)

# ============================================================
# ===================== FONCTIONS UI ==========================
# ============================================================

def dessiner_bouton(surface, rect, texte, actif=True):
    couleur = BOUTON_ACTIF if actif else BOUTON
    pygame.draw.rect(surface, couleur, rect, border_radius=10)
    txt = police.render(texte, True, NOIR)
    surface.blit(txt, (rect.x + 16, rect.y + 14))


def wrap_lines(text, font, max_width):
    """
    Découpe un texte en lignes pour qu'elles tiennent dans max_width.
    """
    words = text.split(" ")
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def draw_card(surface, joueur, est_actif):
    pygame.draw.rect(surface, CARTE_COL, zone_carte, border_radius=12)
    if est_actif:
        pygame.draw.rect(surface, BOUTON_ACTIF, zone_carte, width=4, border_radius=12)

    carte = joueur.carte_visible()

    surface.blit(police.render(joueur.nom, True, NOIR), (30, 26))
    surface.blit(police.render(carte.nom, True, NOIR), (30, 56))

    surface.blit(police.render(f"Poids : {carte.poids}", True, NOIR), (30, 105))
    surface.blit(police.render(f"Longueur : {carte.longueur}", True, NOIR), (30, 135))
    surface.blit(police.render(f"Longévité : {carte.longevite}", True, NOIR), (30, 165))

    surface.blit(police.render(f"Cartes : {len(joueur.cartes)}", True, NOIR), (30, 215))


def robot_joue_si_besoin():
    global ui_state, message_ui
    if game is None:
        return
    if game.terminee:
        ui_state = UI_END
        message_ui = f"🏆 {game.gagnant.nom} gagne la partie !"
        return

    if ui_state == UI_PLAY and game.actif_est_robot():
        carte = game.joueur_actif.carte_visible()
        if game.mode_robot == "A":
            car = choix_robot_aleatoire()
        else:
            car = choix_robot_intelligent(carte, game.historique_cartes)

        game.appliquer_manche(car)

        label = {"poids": "Poids", "longueur": "Longueur", "longevite": "Longévité"}[car]
        message_ui = f"{label} : {game.derniere_val_actif} vs {game.derniere_val_passif} — {game.dernier_gagnant.nom} gagne"
        ui_state = UI_END if game.terminee else UI_RESULT


# ============================================================
# ========================= BOUCLE ============================
# ============================================================

clock = pygame.time.Clock()
running = True

while running:
    robot_joue_si_besoin()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # =========================
        # INPUT PRENOM (START)
        # =========================
        if ui_state == UI_START and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                prenom = prenom[:-1]
            elif event.key == pygame.K_RETURN:
                # pas obligatoire, mais ça valide visuellement
                prenom_actif = False
            else:
                if len(prenom) < 14 and event.unicode.isprintable():
                    # filtrage simple: lettres + espace + tiret
                    if event.unicode.isalnum() or event.unicode in [" ", "-", "_"]:
                        prenom += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            # Overlay règles : clic pour fermer
            if afficher_regles:
                if 80 <= x <= 620 and 60 <= y <= 440:
                    afficher_regles = False
                continue

            # Hamburger
            if bouton_menu.collidepoint(x, y):
                menu_ouvert = not menu_ouvert

            # Options menu
            if menu_ouvert:
                for i, rect in enumerate(option_rects):
                    if rect.collidepoint(x, y - 80):
                        opt = options[i]
                        if opt == "Quitter":
                            running = False
                        elif opt == "Règles":
                            afficher_regles = True
                        elif opt == "Rejouer":
                            ui_state = UI_START
                            game = None
                            message_ui = ""
                            prenom_actif = True
                        menu_ouvert = False

            # START : activation champ + effacer + choix mode
            if ui_state == UI_START:
                if input_rect.collidepoint(x, y):
                    prenom_actif = True
                if clear_rect.collidepoint(x, y):
                    prenom = ""
                    prenom_actif = True

                for label, mode, rect in start_buttons:
                    if rect.collidepoint(x, y):
                        # si PVP, le prénom n'est pas utilisé (mais on le garde)
                        game = creer_partie(mode, prenom=prenom)
                        ui_state = UI_PLAY
                        message_ui = ""
                        menu_ouvert = False
                        break

            # RESULT : clic pour continuer
            elif ui_state == UI_RESULT:
                ui_state = UI_END if (game and game.terminee) else UI_PLAY
                message_ui = ""

            # PLAY : clic carac (seulement si humain actif)
            elif ui_state == UI_PLAY and game is not None and not game.actif_est_robot() and not game.terminee:
                local_x = x - 150
                local_y = y - 80
                for label, key, rect in boutons_carac:
                    if rect.collidepoint(local_x, local_y):
                        game.appliquer_manche(key)
                        message_ui = f"{label} : {game.derniere_val_actif} vs {game.derniere_val_passif} — {game.dernier_gagnant.nom} gagne"
                        ui_state = UI_END if game.terminee else UI_RESULT
                        break

    # =========================
    # AFFICHAGE
    # =========================
    fenetre.fill(FOND)

    frame_haut.fill(VERT_NATURE)
    frame_gauche.fill(PANEL)
    frame_jeu.fill(PANEL)
    frame_j1.fill(PANEL)
    frame_j2.fill(PANEL)

    # Titre
    texte_titre = police_titre.render("Défi Nature", True, BLANC)
    frame_haut.blit(texte_titre, (220, 20))

    # Hamburger
    pygame.draw.rect(frame_haut, PANEL, bouton_menu, border_radius=6)
    icone = police_menu.render("≡" if not menu_ouvert else "×", True, BLANC)
    frame_haut.blit(icone, (bouton_menu.x + 10, bouton_menu.y + 2))

    # Menu gauche
    if menu_ouvert:
        for i, rect in enumerate(option_rects):
            pygame.draw.rect(frame_gauche, FOND, rect, border_radius=8)
            txt = police.render(options[i], True, BLANC)
            frame_gauche.blit(txt, (rect.x + 15, rect.y + 10))

    # START screen
    if ui_state == UI_START:
        fenetre.blit(frame_haut, (0, 0))
        fenetre.blit(frame_gauche, (0, 80))
        fenetre.blit(frame_jeu, (150, 80))

        box = pygame.Rect(170, 110, 510, 360)
        pygame.draw.rect(fenetre, PANEL, box, border_radius=14)
        pygame.draw.rect(fenetre, VERT_NATURE, box, width=3, border_radius=14)

        t = police_menu.render("Choisis un mode", True, BLANC)
        fenetre.blit(t, (box.x + 145, box.y + 18))

        # Champ prénom
        label_prenom = police.render("Ton prénom :", True, BLANC)
        fenetre.blit(label_prenom, (input_rect.x, input_rect.y - 28))

        pygame.draw.rect(fenetre, CARTE_COL, input_rect, border_radius=10)
        pygame.draw.rect(fenetre, BOUTON_ACTIF if prenom_actif else VERT_NATURE, input_rect, width=2, border_radius=10)

        prenom_aff = prenom if prenom else ""
        txt_prenom = police.render(prenom_aff, True, NOIR)
        fenetre.blit(txt_prenom, (input_rect.x + 10, input_rect.y + 12))

        # bouton clear
        pygame.draw.rect(fenetre, BOUTON, clear_rect, border_radius=10)
        fenetre.blit(police_menu.render("×", True, NOIR), (clear_rect.x + 11, clear_rect.y + 5))

        # Boutons modes
        for label, mode, rect in start_buttons:
            dessiner_bouton(fenetre, rect, label, actif=True)

        hint = police_petite.render("Menu ≡ : Rejouer / Règles / Quitter", True, BLANC)
        fenetre.blit(hint, (210, 470))

    else:
        # Jeu en cours
        if game is not None:
            est_actif_j1 = (game.joueur_actif is game.joueurs[0])
            est_actif_j2 = (game.joueur_actif is game.joueurs[1])

            draw_card(frame_j1, game.joueurs[0], est_actif_j1)
            draw_card(frame_j2, game.joueurs[1], est_actif_j2)

            frame_jeu.blit(frame_j1, (0, 0))
            frame_jeu.blit(frame_j2, (frame_j1.get_width() + 10, 0))

            # Bandeau tour
            pygame.draw.rect(frame_jeu, FOND, tour_bar_rect, border_radius=10)
            info = f"Tour de : {game.joueur_actif.nom}"
            if game.actif_est_robot():
                info += " (Robot)"
            txt_info = police.render(info, True, BLANC)
            frame_jeu.blit(txt_info, (tour_bar_rect.x + 12, tour_bar_rect.y + 5))

            # Boutons carac (activés uniquement si humain actif et UI_PLAY)
            boutons_actifs = (ui_state == UI_PLAY and not game.actif_est_robot() and not game.terminee)
            for label, key, rect in boutons_carac:
                couleur = BOUTON_ACTIF if boutons_actifs else BOUTON
                pygame.draw.rect(frame_jeu, couleur, rect, border_radius=8)
                t = police.render(label, True, NOIR)
                frame_jeu.blit(t, (rect.x + 25, rect.y + 10))

            # Message résultat / fin
            if message_ui:
                txt_msg = police_petite.render(message_ui, True, BLANC)
                frame_jeu.blit(txt_msg, (20, frame_jeu.get_height() - 20))

            if ui_state == UI_RESULT:
                txt = police_petite.render("Clique pour continuer…", True, BOUTON_ACTIF)
                frame_jeu.blit(txt, (frame_jeu.get_width() - 190, frame_jeu.get_height() - 20))

            if ui_state == UI_END and game.terminee:
                txt = police_menu.render("FIN", True, BOUTON_ACTIF)
                frame_jeu.blit(txt, (frame_jeu.get_width() - 80, 10))

        fenetre.blit(frame_haut, (0, 0))
        fenetre.blit(frame_gauche, (0, 80))
        fenetre.blit(frame_jeu, (150, 80))

    # Overlay règles : wrap automatique pour ne pas déborder
    if afficher_regles:
        overlay = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        fenetre.blit(overlay, (0, 0))

        regles_frame = pygame.Rect(80, 60, 540, 380)
        pygame.draw.rect(fenetre, PANEL, regles_frame, border_radius=12)
        pygame.draw.rect(fenetre, VERT_NATURE, 3, regles_frame, border_radius=12)

        titre = police_menu.render("Règles du jeu", True, BLANC)
        fenetre.blit(titre, (regles_frame.x + 170, regles_frame.y + 15))

        max_w = regles_frame.width - 40
        y_text = regles_frame.y + 60

        # on adapte la police si vraiment trop long
        font_rules = police_petite
        line_h = 18

        # Construire toutes les lignes wrappées
        lignes = []
        for ligne in regles_texte:
            if not ligne.strip():
                lignes.append("")
                continue
            lignes.extend(wrap_lines(ligne, font_rules, max_w))

        # Si trop de lignes, on réduit légèrement l'interligne (et police)
        max_lines = (regles_frame.height - 110) // line_h
        if len(lignes) > max_lines:
            font_rules = pygame.font.SysFont("arial", 14)
            line_h = 16
            lignes = []
            for ligne in regles_texte:
                if not ligne.strip():
                    lignes.append("")
                    continue
                lignes.extend(wrap_lines(ligne, font_rules, max_w))

        # Affichage (coupure douce si encore trop long)
        max_lines = (regles_frame.height - 110) // line_h
        for i, l in enumerate(lignes[:max_lines]):
            txt = font_rules.render(l, True, BLANC)
            fenetre.blit(txt, (regles_frame.x + 20, y_text))
            y_text += line_h

        fermer = police.render("Cliquez dans la fenêtre pour fermer", True, BOUTON_ACTIF)
        fenetre.blit(fermer, (regles_frame.x + 85, regles_frame.y + 350))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
