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
import numpy as np

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
        all_words = []
        
        for tex_file in tex_files:
            try:
                result = subprocess.run([
                    'git', 'show', f'{commit}:{tex_file}'
                ], capture_output=True, text=True, check=True)
                
                cleaned_text = self.clean_latex_text(result.stdout)
                if cleaned_text:
                    words = cleaned_text.lower().split()
                    normalized_words = []
                    for word in words:
                        clean_word = re.sub(r'[^\w]', '', word)
                        if clean_word.endswith('s'):
                            clean_word = clean_word[:-1]
                        if clean_word:
                            normalized_words.append(clean_word)
                    
                    all_words.extend(normalized_words)
                    total_words += len(words)
                
            except subprocess.CalledProcessError:
                continue
        
        unique_words = len(set(all_words)) if all_words else 0
        return total_words, len(tex_files), unique_words
    
    def get_git_history(self):
        """Récupère l'historique Git"""
        try:
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
                date_result = subprocess.run([
                    'git', 'show', '-s', '--format=%ci', commit
                ], capture_output=True, text=True, check=True)
                
                date_str = date_result.stdout.strip()
                date = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
                
                word_count, file_count, unique_words = self.count_words_at_commit(commit)
                
                msg_result = subprocess.run([
                    'git', 'show', '-s', '--format=%s', commit
                ], capture_output=True, text=True, check=True)
                
                commit_msg = msg_result.stdout.strip()[:50]
                
                self.commits_data.append({
                    'commit': commit[:8],
                    'date': date,
                    'words': word_count,
                    'unique_words': unique_words,
                    'files': file_count,
                    'message': commit_msg
                })
                
                print(f"[{i+1:3d}/{len(commits)}] {date.strftime('%Y-%m-%d')} | "
                      f"{word_count:5d} mots ({unique_words:4d} uniques) | {file_count} fichiers | {commit_msg}")
                
            except subprocess.CalledProcessError as e:
                print(f"Erreur sur commit {commit[:8]}: {e}")
                continue
    
    def create_visualizations(self):
        """Crée les graphiques d'évolution"""
        if not self.commits_data:
            print("Aucune donnée à visualiser!")
            return
        
        df = pd.DataFrame(self.commits_data)
        
        plt.style.use('default')
        magma_colors = ['#0c0826', '#40106c', '#781c6d', '#b73779', '#e65b68', '#f89b5f', '#fcde9c']
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('Evolution du rapport LaTeX', fontsize=14, fontweight='bold')
        
        # Graphique 1: Évolution temporelle
        ax1 = axes[0, 0]
        ax1.plot(df['date'], df['words'], 'o-', linewidth=2.5, markersize=5, 
                color=magma_colors[4], alpha=0.9)
        ax1.set_title('Nombre de mots dans le temps')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Nombre de mots')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax1.tick_params(axis='x', rotation=45)
        
        # Graphique 2: Vitesse d'écriture
        ax2 = axes[0, 1]
        if len(df) > 1:
            df['date_only'] = df['date'].dt.date
            daily_stats = df.groupby('date_only').agg({
                'words': ['first', 'last'],
                'date': 'first'
            }).reset_index()
            
            daily_stats.columns = ['date_only', 'words_start', 'words_end', 'full_date']
            daily_stats['daily_change'] = daily_stats['words_end'] - daily_stats['words_start']
            
            positive_days = daily_stats[daily_stats['daily_change'] > 0]
            negative_days = daily_stats[daily_stats['daily_change'] < 0]
            zero_days = daily_stats[daily_stats['daily_change'] == 0]
            
            bar_width = 0.8
            
            if len(positive_days) > 0:
                ax2.bar(positive_days['full_date'], positive_days['daily_change'], 
                       width=bar_width, color=magma_colors[5], alpha=0.8, 
                       label=f'Jours productifs ({len(positive_days)})', 
                       edgecolor='white', linewidth=0.5)
            
            if len(negative_days) > 0:
                ax2.bar(negative_days['full_date'], negative_days['daily_change'], 
                       width=bar_width, color=magma_colors[2], alpha=0.8, 
                       label=f'Jours de révision ({len(negative_days)})', 
                       edgecolor='white', linewidth=0.5)
            
            if len(zero_days) > 0:
                ax2.bar(zero_days['full_date'], zero_days['daily_change'], 
                       width=bar_width, color=magma_colors[3], alpha=0.8, 
                       label=f'Jours neutres ({len(zero_days)})', 
                       edgecolor='white', linewidth=0.5)
            
            avg_productive = positive_days['daily_change'].mean() if len(positive_days) > 0 else 0
            max_day = daily_stats['daily_change'].max()
            
            ax2.set_title(f'Productivité quotidienne\n(Moy: {avg_productive:.0f} mots, Record: {max_day:.0f})')
            ax2.axhline(0, color='black', linestyle='-', alpha=0.5, linewidth=1)
            
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Mots ajoutés/supprimés par jour')
        ax2.legend(loc='upper left', fontsize=9)
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax2.tick_params(axis='x', rotation=45)
        
        # Graphique 3: Distribution des variations
        ax3 = axes[1, 0]
        if len(df) > 1:
            df_temp = df.copy()
            df_temp['word_diff'] = df_temp['words'].diff()
            word_changes = df_temp['word_diff'].dropna()
            
            n_bins = min(15, max(5, len(word_changes) // 3))
            
            counts, bins, patches = ax3.hist(word_changes, bins=n_bins, 
                                           alpha=0.8, edgecolor='white', linewidth=0.8)
            
            for patch, bin_start, bin_end in zip(patches, bins[:-1], bins[1:]):
                if bin_end <= 0:
                    patch.set_facecolor(magma_colors[1])
                elif bin_start >= 0:
                    patch.set_facecolor(magma_colors[5])
                else:
                    patch.set_facecolor(magma_colors[3])
            
            mean_val = word_changes.mean()
            median_val = word_changes.median()
            
            ax3.axvline(mean_val, color=magma_colors[6], linestyle='--', linewidth=2,
                       label=f'Moyenne: {mean_val:.0f}')
            ax3.axvline(median_val, color=magma_colors[0], linestyle=':', linewidth=2,
                       label=f'Médiane: {median_val:.0f}')
                       
        ax3.set_title('Distribution des variations par commit')
        ax3.set_xlabel('Variation nette de mots')
        ax3.set_ylabel('Fréquence')
        ax3.legend(fontsize=9)
        ax3.grid(True, alpha=0.3)
        from matplotlib.ticker import MaxNLocator
        ax3.xaxis.set_major_locator(MaxNLocator(nbins=15))
        
        # Graphique 4: Richesse du vocabulaire
        ax4 = axes[1, 1]
        if len(df) > 1:
            ax4.plot(df['date'], df['unique_words'], 'o-', linewidth=2.5, markersize=5, 
                    color=magma_colors[3], alpha=0.9, label='Mots uniques')
            
            ax4_twin = ax4.twinx()
            richness_ratio = df['unique_words'] / df['words'] * 100
            ax4_twin.plot(df['date'], richness_ratio, 's--', linewidth=2, markersize=4, 
                         color=magma_colors[5], alpha=0.7, label='Richesse (%)')
            
            ax4.set_xlabel('Date')
            ax4.set_ylabel('Nombre de mots uniques', color=magma_colors[3])
            ax4_twin.set_ylabel('Richesse du vocabulaire (%)', color=magma_colors[5])
            
            ax4.tick_params(axis='y', labelcolor=magma_colors[3])
            ax4_twin.tick_params(axis='y', labelcolor=magma_colors[5])
            
            final_richness = richness_ratio.iloc[-1]
            ax4.set_title(f'Richesse du vocabulaire\n(Actuelle: {final_richness:.1f}%)')
            
        else:
            ax4.text(0.5, 0.5, 'Données insuffisantes', ha='center', va='center',
                    transform=ax4.transAxes, fontsize=12)
            ax4.set_title('Richesse du vocabulaire')
        
        ax4.grid(True, alpha=0.3)
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax4.tick_params(axis='x', rotation=45)
        
        # Layout
        plt.tight_layout(pad=1.5)
        plt.subplots_adjust(top=0.93)
        
        plt.savefig('word_evolution.png', dpi=200, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.show()
        
        df.to_csv('word_history.csv', index=False)
        print(f"\nDonnées sauvées dans word_history.csv")
        print(f"Graphique sauvé dans word_evolution.png")

def main():
    """Fonction principale"""
    print("Analyseur d'évolution LaTeX")
    print("=" * 40)
    
    if not Path('.git').exists():
        print("Ce n'est pas un repository Git!")
        return
    
    tracker = LaTeXWordTracker()
    tracker.analyze_repository()
    tracker.create_visualizations()
    
    print("\nAnalyse terminée!")

if __name__ == "__main__":
    main()