# Stratégie de test — MiniShop

> Modèle à compléter pendant l'Atelier 12. Une stratégie de test tient sur 2 pages : si elle est plus longue, personne ne la lit.

## 1. Périmètre et risques
| Zone | Risque métier | Probabilité | Impact | Niveau de test principal |
|---|---|---|---|---|
| Calcul des prix (`pricing.py`) | Mauvais montant facturé | Moyenne | Élevé | Unitaire + génération IA |
| API commandes | Commande perdue | Faible | Élevé | API + contrat |
| Interface | Parcours bloqué | Moyenne | Moyen | E2E + visuel |
| Performance | Abandon de panier | … | … | Charge (Locust/JMeter) |
| Sécurité | Fuite / injection | … | … | SAST, SCA, DAST (ZAP) |

## 2. Pyramide et quality gates
| Étape pipeline | Tests | Seuil bloquant |
|---|---|---|
| PR | lint, unitaires, API | 100 % OK, couverture ≥ 85 % |
| main | + E2E, visuel, sécurité | 0 vulnérabilité HIGH/CRITICAL |
| nocturne | charge, ZAP complet | p95 < 300 ms, erreurs < 1 % |

## 3. Règles pour les tests générés par IA
- Un test généré est **relu** avant fusion (marqueur `@pytest.mark.generated`).
- Il doit échouer si on casse la règle qu'il prétend vérifier (vérifié par mutation).
- Pas de secret ni de donnée client dans les prompts.

## 4. Gestion des tests instables (flaky)
- Détection : `ai_tools/test_history.py` (score ≥ 0,6).
- Quarantaine : marqueur `flaky`, ticket ouvert, délai de correction 5 jours.

## 5. Indicateurs suivis
Taux de réussite sur main, durée de la suite, nombre de tests flaky, couverture, MTTR d'une régression.


## 3. Règles pour les tests générés par IA

### Relecture et validation
- Tout test généré par IA doit être relu par un développeur.
- Vérifier que le test correspond aux règles métier.
- Vérifier que les fonctions utilisées existent réellement.
- Contrôler les assertions et les résultats attendus.
- Les tests doivent passer avant leur intégration.

### Identification des tests
- Les tests générés doivent porter le marqueur
  `@pytest.mark.generated`.
- Ils sont conservés dans `tests/generated/`.
- Leur origine (modèle, prompt) doit être documentée.

### Qualité des tests
- Mesurer la couverture des tests générés.
- Utiliser les tests de mutation pour vérifier leur efficacité.
- Ne pas accepter un test uniquement parce qu'il passe.
- Tout échec doit être analysé avant correction.

### Sécurité et confidentialité
- Ne jamais transmettre de clés API, mots de passe
  ou données personnelles dans les prompts.
- Ne pas envoyer de code confidentiel à un LLM externe
  sans autorisation.

### Responsabilité
- Le développeur qui valide le test reste responsable
  de son exactitude.
- Un test généré incorrect doit être corrigé ou supprimé.
- L'IA est une aide à la création, pas une validation
  automatique du comportement métier.

