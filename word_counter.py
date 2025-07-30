#!/usr/bin/env python3
"""
Traceur d'évolution du nombre de mots dans un repo LaTeX
Usage: python word_tracker.py
"""

import subprocess
import re
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from pathlib import Path

class LaTeXWordTracker:
    def __init__(self):
        self.commits_data = []
        
    def clean_latex_text(self, text):
        """Nettoie le texte LaTeX pour compter seulement le contenu réel"""
        # Supprime les commentaires
        text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
        
        # Supprime les commandes LaTeX avec arguments
        text = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})*', '', text)
        
        # Supprime les formules mathématiques
        text = re.sub(r'\$\$.*?\$\$', '', text, flags=re.DOTALL)
        text = re.sub(r'\$[^$]*\$', '', text)
        text = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', '', text, flags=re.DOTALL)
        text = re.sub(r'\\begin\{align\}.*?\\end\{align\}', '', text, flags=re.DOTALL)
        
        # Supprime les environnements de code
        text = re.sub(r'\\begin\{verbatim\}.*?\\end\{verbatim\}', '', text, flags=re.DOTALL)
        text = re.sub(r'\\begin\{lstlisting\}.*?\\end\{lstlisting\}', '', text, flags=re.DOTALL)
        
        # Supprime les références bibliographiques
        text = re.sub(r'\\cite\{[^}]*\}', '', text)
        text = re.sub(r'\\ref\{[^}]*\}', '', text)
        text = re.sub(r'\\label\{[^}]*\}', '', text)
        
        # Supprime les accolades restantes
        text = re.sub(r'[{}]', '', text)
        
        # Supprime les caractères de contrôle et espaces multiples
        text = re.sub(r'[\\&_^#]', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def get_tex_files_at_commit(self, commit):
        """Récupère tous les fichiers .tex à un commit donné"""
        try:
            result = subprocess.run([
                'git', 'ls-tree', '-r', '--name-only', commit
            ], capture_output=True, text=True, check=True)
            
            tex_files = [f for f in result.stdout.strip().split('\n') 
                        if f.endswith('.tex') and f]
            return tex_files
        except subprocess.CalledProcessError:
            return []
    
    def count_words_at_commit(self, commit):
        """Compte les mots dans tous les fichiers .tex à un commit donné"""
        tex_files = self.get_tex_files_at_commit(commit)
        total_words = 0
        
        for tex_file in tex_files:
            try:
                result = subprocess.run([
                    'git', 'show', f'{commit}:{tex_file}'
                ], capture_output=True, text=True, check=True)
                
                cleaned_text = self.clean_latex_text(result.stdout)
                words = len(cleaned_text.split()) if cleaned_text else 0
                total_words += words
                
            except subprocess.CalledProcessError:
                continue
        
        return total_words, len(tex_files)
    
    def get_git_history(self):
        """Récupère l'historique Git"""
        try:
            # Récupère tous les commits
            result = subprocess.run([
                'git', 'rev-list', '--reverse', '--all'
            ], capture_output=True, text=True, check=True)
            
            commits = result.stdout.strip().split('\n')
            return [c for c in commits if c]
        except subprocess.CalledProcessError:
            print("Erreur: Impossible de récupérer l'historique Git")
            return []
    
    def analyze_repository(self):
        """Analyse complète du repository"""
        commits = self.get_git_history()
        
        if not commits:
            print("Aucun commit trouvé!")
            return
        
        print(f"Analyse de {len(commits)} commits...")
        
        for i, commit in enumerate(commits):
            try:
                # Récupère la date du commit
                date_result = subprocess.run([
                    'git', 'show', '-s', '--format=%ci', commit
                ], capture_output=True, text=True, check=True)
                
                date_str = date_result.stdout.strip()
                date = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
                
                # Compte les mots
                word_count, file_count = self.count_words_at_commit(commit)
                
                # Récupère le message de commit
                msg_result = subprocess.run([
                    'git', 'show', '-s', '--format=%s', commit
                ], capture_output=True, text=True, check=True)
                
                commit_msg = msg_result.stdout.strip()[:50]
                
                self.commits_data.append({
                    'commit': commit[:8],
                    'date': date,
                    'words': word_count,
                    'files': file_count,
                    'message': commit_msg
                })
                
                print(f"[{i+1:3d}/{len(commits)}] {date.strftime('%Y-%m-%d')} | "
                      f"{word_count:5d} mots | {file_count} fichiers | {commit_msg}")
                
            except subprocess.CalledProcessError as e:
                print(f"Erreur sur commit {commit[:8]}: {e}")
                continue
    
    def create_visualizations(self):
        """Crée les graphiques d'évolution"""
        if not self.commits_data:
            print("Aucune donnée à visualiser!")
            return
        
        df = pd.DataFrame(self.commits_data)
        
        # Configuration du style
        plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('📝 Évolution du rapport LaTeX', fontsize=16, fontweight='bold')
        
        # Graphique 1: Évolution temporelle
        ax1 = axes[0, 0]
        ax1.plot(df['date'], df['words'], 'o-', linewidth=2, markersize=4, 
                color='#2E86AB', alpha=0.8)
        ax1.set_title('🚀 Nombre de mots dans le temps')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Nombre de mots')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.tick_params(axis='x', rotation=45)
        
        # Graphique 2: Vitesse d'écriture (agrégée par jour)
        ax2 = axes[0, 1]
        if len(df) > 1:
            # Agrégation par jour
            df['date_only'] = df['date'].dt.date
            daily_stats = df.groupby('date_only').agg({
                'words': ['first', 'last'],  # premier et dernier mot count du jour
                'date': 'first'  # pour garder la date complète
            }).reset_index()
            
            # Aplatit les colonnes multi-niveau
            daily_stats.columns = ['date_only', 'words_start', 'words_end', 'full_date']
            
            # Calcule le changement net par jour
            daily_stats['daily_change'] = daily_stats['words_end'] - daily_stats['words_start']
            
            # Sépare positif/négatif
            positive_days = daily_stats[daily_stats['daily_change'] > 0]
            negative_days = daily_stats[daily_stats['daily_change'] <= 0]
            zero_days = daily_stats[daily_stats['daily_change'] == 0]
            
            # Barres avec largeur d'une journée
            bar_width = 0.8  # 80% d'une journée
            
            if len(positive_days) > 0:
                ax2.bar(positive_days['full_date'], positive_days['daily_change'], 
                       width=bar_width, color='#4ECDC4', alpha=0.8, 
                       label=f'Jours productifs ({len(positive_days)})', 
                       edgecolor='white', linewidth=0.5)
            
            if len(negative_days) > 0:
                ax2.bar(negative_days['full_date'], negative_days['daily_change'], 
                       width=bar_width, color='#FF6B6B', alpha=0.8, 
                       label=f'Jours de révision ({len(negative_days)})', 
                       edgecolor='white', linewidth=0.5)
            
            if len(zero_days) > 0:
                ax2.bar(zero_days['full_date'], zero_days['daily_change'], 
                       width=bar_width, color='#FFE66D', alpha=0.8, 
                       label=f'Jours neutres ({len(zero_days)})', 
                       edgecolor='white', linewidth=0.5)
            
            # Stats dans le titre
            avg_productive = positive_days['daily_change'].mean() if len(positive_days) > 0 else 0
            max_day = daily_stats['daily_change'].max()
            
            ax2.set_title(f'✍️ Productivité quotidienne\n(Moy. productive: {avg_productive:.0f} mots, Record: {max_day:.0f})')
            
            # Ligne de référence
            ax2.axhline(0, color='black', linestyle='-', alpha=0.5, linewidth=1)
            
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Mots ajoutés/supprimés par jour')
        ax2.legend(loc='upper left', fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        # Format des dates plus espacé
        ax2.xaxis.set_major_locator(mdates.WeekdayLocator())
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax2.tick_params(axis='x', rotation=45)
        
        # Graphique 3: Distribution des tailles de commits
        ax3 = axes[1, 0]
        if len(df) > 1:
            # Calcule word_diff ici aussi pour ce graphique
            df_temp = df.copy()
            df_temp['word_diff'] = df_temp['words'].diff()
            word_changes = df_temp['word_diff'].dropna()
            
            # Calcul intelligent du nombre de bins
            n_bins = min(15, max(5, len(word_changes) // 3))
            
            # Histogramme avec barres séparées
            counts, bins, patches = ax3.hist(word_changes, bins=n_bins, 
                                           color='#FFB3BA', alpha=0.7, 
                                           edgecolor='black', linewidth=0.8,
                                           rwidth=0.8)  # espace entre barres
            
            # Colorie différemment les gains/pertes
            for i, (patch, bin_start, bin_end) in enumerate(zip(patches, bins[:-1], bins[1:])):
                if bin_end <= 0:
                    patch.set_facecolor('#FF6B6B')  # Rouge pour pertes
                elif bin_start >= 0:
                    patch.set_facecolor('#4ECDC4')  # Vert pour gains
                else:
                    patch.set_facecolor('#FFE66D')  # Jaune pour mixte
            
            # Ligne de moyenne
            mean_val = word_changes.mean()
            ax3.axvline(mean_val, color='darkred', linestyle='--', linewidth=2,
                       label=f'Moyenne: {mean_val:.0f}')
            
            # Ligne médiane
            median_val = word_changes.median()
            ax3.axvline(median_val, color='darkblue', linestyle=':', linewidth=2,
                       label=f'Médiane: {median_val:.0f}')
                       
        ax3.set_title('📊 Distribution des changements par commit')
        ax3.set_xlabel('Changement de mots par commit')
        ax3.set_ylabel('Fréquence')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Améliore les ticks pour éviter la surcharge
        ax3.tick_params(axis='x', rotation=45)
        
        # Graphique 4: Statistiques
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        # Calcul des stats d'abord
        total_words = df['words'].iloc[-1]
        start_date = df['date'].min().strftime('%Y-%m-%d')
        end_date = df['date'].max().strftime('%Y-%m-%d')
        duration = (df['date'].max() - df['date'].min()).days
        total_commits = len(df)
        max_files = df['files'].max()
        
        # Calcul de la vitesse moyenne basée sur l'agrégation quotidienne
        if len(df) > 1:
            total_word_change = df['words'].iloc[-1] - df['words'].iloc[0]
            avg_rate = total_word_change / max(duration, 1)
            
            # Record basé sur les commits individuels
            df_temp = df.copy()
            df_temp['word_diff'] = df_temp['words'].diff()
            max_commit_change = df_temp['word_diff'].max()
        else:
            avg_rate = max_commit_change = 0
        
        stats_text = f"""📈 STATISTIQUES DU PROJET
        
🎯 Total actuel: {total_words:,} mots
📅 Période: {start_date} → {end_date}
⏱️ Durée: {duration} jours
📝 Commits: {total_commits}
📁 Fichiers max: {max_files}

🏆 Plus gros commit: {max_commit_change:.0f} mots
📊 Moyenne quotidienne: {avg_rate:.0f} mots/jour"""
        
        ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", 
                facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig('word_evolution.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Sauvegarde CSV
        df.to_csv('word_history.csv', index=False)
        print(f"\n💾 Données sauvées dans word_history.csv")
        print(f"🖼️ Graphique sauvé dans word_evolution.png")

def main():
    """Fonction principale"""
    print("🔍 Analyseur d'évolution LaTeX")
    print("=" * 40)
    
    # Vérification que c'est un repo Git
    if not Path('.git').exists():
        print("❌ Ce n'est pas un repository Git!")
        return
    
    tracker = LaTeXWordTracker()
    tracker.analyze_repository()
    tracker.create_visualizations()
    
    print("\n✅ Analyse terminée!")

if __name__ == "__main__":
    main()