"""Display results and analysis"""

__author__ = 'Charlie Guthrie'

import numpy as np
import pandas as pd
import cPickle as pickle
import matplotlib.pyplot as plt
import seaborn as sns

CONTEXT='notebook'

def get_results_df(result_path):
    log = pickle.load(open( result_path, "rb" ))
    raw_df = pd.DataFrame.from_dict(log)
    available_columns = list(raw_df.columns)
    desired_columns = ['strat_column','strat_value','model','best_score','train_accuracy','test_accuracy','num_cases','num_features','num_opinion_shards']
    desired_and_available = list(set(desired_columns) & set(available_columns))
    df = raw_df[desired_and_available]
    return df

def print_weighted_accuracy(df):
    models = df['model'].unique()
    for model in models:
        mdf = df.loc[df['model']==model,:]
        total_cases = sum(mdf['num_cases'])
        weighted_accuracy = sum(mdf['test_accuracy']*mdf['num_cases']/total_cases)
        print "model: %s, weighted accuracy: %s%%" %(model,round(weighted_accuracy*100,1))

def identify_best_of_each_model(df,metric):
    baseline_scores = {'best_score':'train_accuracy','test_accuracy':'test_accuracy'}
    score_list = []
    models = df['model'].unique()
    print "Best values for each model:"
    for model in models:
        df2 = df.loc[df['model']==model]
        if model=='baseline':
            best_score=max(df2[baseline_scores[metric]])
            print df2.loc[df2[baseline_scores[metric]]==best_score,('model','best_params')].values[0]
        else:
            best_score = max(df2[metric])
            print df2.loc[df2[metric]==best_score,('model','best_params')].values[0]
        score_list.append(best_score)
        
        
    return models,score_list

def best_model_accuracy_bars(df,fig_path,metric,context):
    '''
    df: data frame
    context: paper,talk, notebook, poster
    '''
    
    font_size = {
        'paper':8,
        'poster':16,
        'notebook':10,
        'talk':13
    }
    sns.set_context(context)
    model_list,score_list = identify_best_of_each_model(df,metric)
    
    #size and position of bars
    bar_pos = np.arange(len(model_list))
    bar_size = score_list
    bar_labels = model_list
    
    #plot
    fig = plt.figure()
    plt.barh(bar_pos,bar_size, align='center', alpha=0.4)
    plt.yticks(bar_pos, bar_labels)
    plt.xticks([],[]) #no x-axis

    #Add data labels
    for x,y in zip(bar_size,bar_pos):
        plt.text(x+0.01, y, '%.2f' % x, ha='left', va='center',fontsize=font_size[context])
        
    pretty_metric = {'test_accuracy':'Test','best_score':'CV'}
    plt.title('Optimized %s Accuracy of Each Model' % pretty_metric[metric])
    fig.savefig(fig_path, bbox_inches='tight')

def main():
    STRATIFIED_RESULT_PATH = "../results/model_results.pkl.20150510-022044.20150510-022044.min_required_count.50.all_features.accuracy"
    UNSTRAT_RESULT_PATH = "../results/model_results.pkl.20150509-052203.20150509-052203.min_required_count.100.chi2.accuracy.geniss"
    RESULTS_CSV_PATH="../results/stratified_results.csv"
    CONTEXT='notebook'

    sdf=get_results_df(STRATIFIED_RESULT_PATH)
    print "Stratified model results saved to %s" %RESULTS_CSV_PATH
    sdf.to_csv(RESULTS_CSV_PATH)
    print_weighted_accuracy(sdf)

    df = get_results_df(UNSTRAT_RESULT_PATH)
    fig_path="../results/stratified_best_score.png"
    best_model_accuracy_bars(df,fig_path,'best_score',CONTEXT)
    fig_path="../results/stratified_test_accuracy.png"
    best_model_accuracy_bars(df,fig_path,'test_accuracy',CONTEXT)

if __name__ == '__main__':
    main()