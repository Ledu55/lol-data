# Modelo do score

AUC fora da amostra (quanto o score separa vitórias de derrotas):

- **BOTTOM**: score completo AUC=0.957; score de rota AUC=0.867
  - pesos principais: kda +3.26, gold_pm_diff +2.24, dmg_share -1.33, kp -1.21, obj_dmg_pm +0.94, dmg_pm +0.92
- **JUNGLE**: score completo AUC=0.959; score de rota AUC=0.854
  - pesos principais: kda +3.17, gold_pm_diff +1.64, dmg_share -1.46, dmg_pm +1.11, kp -0.93, obj_dmg_pm +0.90
- **MIDDLE**: score completo AUC=0.934; score de rota AUC=0.834
  - pesos principais: kda +3.14, dmg_share -1.36, gold_pm_diff +1.27, kp -1.04, dmg_pm +0.88, plates +0.68
- **TOP**: score completo AUC=0.930; score de rota AUC=0.811
  - pesos principais: kda +2.84, gold_pm_diff +1.89, dmg_share -1.56, kp -1.17, dmg_pm +0.84, max_cs_adv -0.54
- **UTILITY**: score completo AUC=0.954; score de rota AUC=0.861
  - pesos principais: gold_pm_diff +2.62, kda +1.81, dmg_share -1.64, dmg_pm +1.36, kp -0.91, dmg_pm_diff -0.78