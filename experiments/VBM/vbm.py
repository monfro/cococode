# created by Eduard Ort, 2019 
#######################
###  import libraries  ###
#######################
from psychopy import visual, core, event,gui,logging #import some libraries from PsychoPy
import expTools as et # custom scripts
import json # to load configuration files
import sys, os # to interact with the operating system
from datetime import datetime # to get the current time
import numpy as np # to do fancy math shit
import glob # to search in system efficiently
from IPython import embed as shell # for debugging
import pandas as pd # efficient table operations

# reset all triggers to zero
os.system("/usr/local/bin/parashell 0x378 0")
#######################################
###  load config file (settings)  #####
#######################################
try:
    jsonfile = sys.argv[1]
except IndexError as e:
    print("No config file provided. Stop it here.")
    sys.exit(-1)
try:
    with open(jsonfile) as f:    
        param = json.load(f)
except FileNotFoundError as e:
    print("{} is not a valid config file. Stop it here.".format(jsonfile))
    sys.exit(-1)

###########################################
###  Create Parameters / do Overhead   ####
###########################################

# read out json sidecar
n_trials = param['n_trials']            # number trials per block
n_blocks = param['n_blocks']            # number total blocks
fix_mean = param['fix_mean']            # presentation duration of fixdot
fix_range = param['fix_range']          # presentation duration of fixdot
select_mean = param['select_mean']          # presentation duration of selection box
select_range = param['select_range']        # presentation duration of selection box
feed_sleep = param['feed_sleep']        # presentation duration of feedback
sess_type = param['sess_type']          # are we practicing or not
trigger = param['trigger']              # trigger for defined events
bar = param['progress_bar']              # trigger for defined events

# dialog with participants: Retrieve Subject number, session number, and practice
input_dict = dict(sub_id=0,sess_id=0,sess_type=sess_type)
inputGUI =gui.DlgFromDict(input_dict,title='Experiment Info',order=['sub_id','sess_id','sess_type'])
# check for input
if inputGUI.OK == False:
    print("Experiment aborted by user")
    core.quit()
while input_dict['sess_id'] not in [1,2,3]:
    print('WARNING: You need to specify a session number (1,2,3)')
    inputGUI.show()
    if inputGUI.OK == False:
        print("Experiment aborted by user")
        core.quit()

# check whether settings match config file
if sess_type!=input_dict['sess_type']:
    print('WARNING: specified session type does not fit config file. This might cause issues further down the stream...')
    logging.warning('WARNING: specified session type does not fit config file. This might cause issues further down the stream...')

# prepare the logfile (general log file, not data log file!) and directories
et.prepDirectories()
log_file = os.path.join('log',param['log_file'].format(input_dict['sub_id'],input_dict['sess_id'],datetime.now()).replace(' ','-').replace(':','-'))
lastLog = logging.LogFile(log_file, level=logging.INFO, filemode='w')
# create a output file that collects all variables 
output_file = os.path.join('dat',param['exp_id'],param['output_file'].format(input_dict['sub_id'],input_dict['sess_id'],datetime.now()).replace(' ','-').replace(':','-'))

# init logger:  update the constant values (things that wont change)
trial_info = {"sub_id":input_dict['sub_id'],
                "sess_id":input_dict['sess_id'],
                "sess_type":input_dict['sess_type'],
                'total_points':0,
                "start_exp_time":core.getTime(),
                "end_block_time":np.nan}
# add variables to the logfile that are defined in config file
for vari in param['logVars']:
    trial_info[vari] = param[vari]
trial_info['log_file'] = log_file
trial_info['output_file'] = output_file

###########################################
###  Prepare Experimental Sequence     ####
###########################################

# load sequence info
sequence = pd.read_csv(param['sequence'])
sequence.prob1 = 100*sequence.prob1
sequence.prob2 = 100*sequence.prob2
# shuffle
sequence = sequence.sample(frac=1).reset_index(drop=True)

if param['resp_mode'] == 'meg':
    resp_left = param['resp1_button']
    resp_right = param['resp2_button']
    pause_resp = param['pause_button']
else:
    resp_left = param['resp1_key']
    resp_right = param['resp2_key']
    pause_resp = param['pause_key']
resp_keys = [resp_left,resp_right]

# convert timing to frames
pause_frames = round(param['pause_sleep']*param['framerate'])
feed_frames = round(param['feed_sleep']*param['framerate'])
resp_frames = round(param['resp_timeout']*param['framerate'])

# make a sequence of fix-stim jitter
fix_seq = np.random.uniform(fix_mean-fix_range,fix_mean+fix_range, size=(n_blocks,n_trials))
fix_frames_seq = (fix_seq*param['framerate']).round().astype(int)
select_seq = np.random.uniform(select_mean-select_range,select_mean+select_range, size=(n_blocks,n_trials))
select_frames_seq = (select_seq*param['framerate']).round().astype(int)

####################
###  experiment  ###
####################
#create a window
win = visual.Window(size=param['win_size'],color=param['bg_color'],fullscr=trial_info['fullscreen'], units="pix",screen=1)

#########################
###  prepare stimuli  ###
#########################
startBlock = visual.TextStim(win,text=param['startBlock_text'],color=param['fg_color'],wrapWidth=win.size[0])
endBlock = visual.TextStim(win,text= param['endBlock_text'],color=param['fg_color'],wrapWidth=win.size[0])
endExp = visual.TextStim(win,text=param['endExp_text'],color=param['fg_color'],wrapWidth=win.size[0])
progress_bar =visual.Rect(win,width=bar['width'],height=bar['height'],lineColor=bar['color'],fillColor=bar['color'],pos = [-bar['horiz_dist'],-bar['vert_dist']])
progress_update =visual.Rect(win,width=bar['width'],height=bar['height'],lineColor=bar['color'],fillColor=bar['color'],pos = [-bar['horiz_dist'],-bar['vert_dist']])
progress_bar_start=visual.Rect(win,width=bar['width'],height=bar['height'],lineColor=bar['color'],fillColor=bar['color'],pos = [-bar['horiz_dist'],-bar['vert_dist']])
progress_bar_end =visual.Rect(win,width=bar['width'],height=bar['height'],lineColor=bar['color'],fillColor=bar['color'],pos = [bar['horiz_dist'],-bar['vert_dist']])
fixDot = et.fancyFixDot(win, bg_color = param['bg_color']) 
leftframe = visual.Rect(win,width=param['select_width'],height=param['select_height'],lineColor=param['fg_color'],fillColor=param['bg_color'],pos = [-param['select_x'],param['select_y']])
rightframe = visual.Rect(win,width=param['select_width'],height=param['select_height'],lineColor=param['fg_color'],fillColor=param['bg_color'],pos = [param['select_x'],param['select_y']])
leftbar = visual.Rect(win,width=param['select_width'],height=param['select_height'],lineColor=param['fg_color'],fillColor=param['fg_color'],pos = [-param['select_x'],param['select_y']])
rightbar = visual.Rect(win,width=param['select_width'],height=param['select_height'],lineColor=param['fg_color'],fillColor=param['fg_color'],pos = [param['select_x'],param['select_y']])
selectbar = visual.Rect(win,width=param['select_width']*1.2,height=param['select_height']*1.5,lineColor=param['fg_color'],fillColor=param['bg_color'],pos = [param['select_x'],-0.1*param['select_height']])
leftProb = visual.TextStim(win,text='',color=param['fg_color'], pos = [-param['select_x'],-param['select_x']] )
rightProb = visual.TextStim(win,text='',color=param['fg_color'], pos = [param['select_x'],-param['select_x']])
timeout_screen = visual.TextStim(win,text='Zu langsam!',color='white',wrapWidth=win.size[0])

# set Mouse to be invisible
event.Mouse(win=None,visible=False)
event.clearEvents()

# experimental phases (unique things on screen)
fix_phase = fixDot[:] +[progress_bar,progress_bar_start,progress_bar_end]
stim_phase = fixDot[:] + [progress_bar,progress_bar_start,progress_bar_end,leftframe,rightframe,leftbar,rightbar,leftProb,rightProb]
select_phase = fixDot[:] +[progress_bar,progress_bar_start,progress_bar_end,selectbar,rightframe,leftframe,leftbar,rightbar,leftProb,rightProb]
feedback_phase = fixDot[:] +[progress_bar,progress_bar_start,progress_bar_end,progress_update,selectbar,rightframe,leftframe,leftbar,rightbar,leftProb,rightProb]

####################
###  block loop  ###
####################
for block_no in range(n_blocks):
    trial_info['block_no']=block_no+1
    
    # start block message
    if param['run_mode'] != 'dummy':
        while True:
            startBlock.text = param["startBlock_text"].format(block_no+1)
            startBlock.draw()
            trial_info['start_block_time'] = win.flip()                        
            cont=et.captureResponse(mode=param['resp_mode'],keys = [pause_resp])    
            if cont == pause_resp:
                break
        et.sendTriggers(trigger['start_block'],mode=param['resp_mode'])
    # get trial info for entire block
    trial_seq = sequence[block_no*n_trials:(block_no+1)*n_trials]

    ####################
    ###  trial loop  ###
    ####################
    for trial_no in range(n_trials):
        # force quite experiment
        escape = event.getKeys()
        if 'q' in escape:
            et.finishExperiment(win,data_logger)

        # reset variables
        reward=0
        response =None
        leftbar.fillColor = param['fg_color']
        rightbar.fillColor = param['fg_color']
        # set trial variables
        trial_info['trial_no'] = trial_no+1
        trial_info['trial_count']+=1
        trial_info['fix_sleep'] = fix_seq[block_no,trial_no]
        trial_info['select_sleep'] = select_seq[block_no,trial_no]
        trial_info['corr_resp'] = resp_keys[int((trial_seq.iloc[trial_no].CorrectLeftRight)-1)]
        trial_info['mag_left'] = trial_seq.iloc[trial_no].mag1
        trial_info['mag_right']= trial_seq.iloc[trial_no].mag2
        trial_info['prob_left'] = trial_seq.iloc[trial_no].prob1
        trial_info['prob_right'] = trial_seq.iloc[trial_no].prob2
        trial_info['rew_left'] = trial_seq.iloc[trial_no].fb1
        trial_info['rew_right'] = trial_seq.iloc[trial_no].fb2
        trial_info['ev_left'] = trial_seq.iloc[trial_no].ev1
        trial_info['ev_right'] = trial_seq.iloc[trial_no].ev2
        trial_info['nb'] = trial_seq.iloc[trial_no]['Nb']
        trial_info['corrSM'] = trial_seq.iloc[trial_no].CorrectLeftRight
        
        fix_frames = fix_frames_seq[block_no,trial_no]
        select_frames = select_frames_seq[block_no,trial_no]
        # set stimulus
        leftbar.height = 10*trial_info['mag_left']
        leftbar.pos = [-param['select_x'],-0.5*param['select_height']+5*trial_info['mag_left']]
        rightbar.height = 10* trial_info['mag_right']
        rightbar.pos = [param['select_x'],-0.5*param['select_height']+5*trial_info['mag_right']]
        leftProb.text =  '{:02d}%'.format(int(trial_info['prob_left']))
        rightProb.text = '{:02d}%'.format(int(trial_info['prob_right']))

        # fix phase
        et.drawCompositeStim(fix_phase)
        trial_info['start_trial_time']=win.flip()
        et.sendTriggers(trigger['start_trial'],mode=param['resp_mode'])          
        for frame in range(fix_frames):
            et.drawCompositeStim(fix_phase)
            trial_info['start_stim_time']=win.flip()  
        trial_info['fixDur'] =  core.getTime()-trial_info['start_trial_time']
        # clear any pending key presses
        event.clearEvents()

        # do it framewise rather than timeout based       
        if param['run_mode']=='dummy':
            dummy_resp_frame = np.random.choice(range(resp_frames+20))
        
        # stimulus phase
        et.drawCompositeStim(stim_phase) 
        # start response time measure
        trial_info['start_stim_time'] = win.flip() 
        et.sendTriggers(trigger['start_stim'],mode=param['resp_mode'])   
        for frame in range(resp_frames):        
            if frame==resp_frames:
                et.drawCompositeStim(fix_phase)
            else:
                et.drawCompositeStim(stim_phase)
            trial_info['end_stim_time'] = win.flip()

            #sample response
            if param['run_mode']=='dummy':
                if dummy_resp_frame == frame:
                    response = np.random.choice(resp_keys)
            else:
                response = et.captureResponse(mode=param['resp_mode'],keys=resp_keys)

            # break if responded
            if response in resp_keys:
                break  

        ##########################
        ###  POST PROCESSING   ###
        ##########################
        # start handling response variables        
        trial_info['start_select_time'] = core.getTime()
        trial_info['resp_time'] = trial_info['start_select_time']-trial_info['start_stim_time']
        trial_info['resp_key'] = response
        trial_info['correct'] = int(response==trial_info['corr_resp'])
        
        if trial_info['resp_key'] == resp_keys[0]:
            selectbar.pos = [-param['select_x'], -0.1*param['select_height']]
        elif trial_info['resp_key'] == resp_keys[1]:
            selectbar.pos = [param['select_x'], -0.1*param['select_height']]

        # draw selection phase if response given
        if response in resp_keys:
            trial_info['timeout'] = 0
            et.drawCompositeStim(select_phase)
            trial_info['start_select_time'] = win.flip()  
            et.sendTriggers(trigger['start_select'],mode=param['resp_mode'])
            for frame in range(select_frames):
                et.drawCompositeStim(select_phase)
                win.flip()  
        else:
            trial_info['timeout'] = 1
            timeout_screen.draw() 
            trial_info['start_select_time'] = win.flip()
            et.sendTriggers(trigger['timeout'],mode=param['resp_mode'])   
            for frame in range(select_frames-1):
                timeout_screen.draw() 
                win.flip() 
        trial_info['selectDur'] =  core.getTime()-trial_info['start_select_time']

            # define incremental reward value
        if trial_info['resp_key']==resp_keys[0] and trial_info['rew_left']:
            reward = trial_info['mag_left']
        elif trial_info['resp_key']==resp_keys[1] and trial_info['rew_right']:
            reward = trial_info['mag_right']
        trial_info['total_points'] += reward
        
        # show update bar
        progress_update.pos = (progress_bar.width + progress_bar_start.pos[0]- progress_bar_start.width/2+ 0.75*reward,progress_bar_start.pos[1])
        progress_update.width =1.5*reward
        progress_update.fillColor =bar['color']
        progress_update.lineColor =bar['color']
        progress_bar.width += 1.5*reward
        progress_bar.pos[0] += 0.75*reward
        if progress_bar.width > 2*bar['horiz_dist']:
            progress_bar.width=bar['width']
            progress_bar.pos[0] = -bar['horiz_dist']                
        elif progress_bar.width < bar['width']:
            progress_bar.width=bar['width']
            progress_bar.pos[0] = -bar['horiz_dist']

        # draw feedback_phase phase
        if trial_info['rew_left'] == 1:
            leftbar.fillColor = bar['corr_color']
        else:
            leftbar.fillColor = bar['incorr_color']
        if trial_info['rew_right'] == 1:
            rightbar.fillColor = bar['corr_color']
        else:
            rightbar.fillColor = bar['incorr_color']
 
        et.drawCompositeStim(feedback_phase)
        trial_info['start_feed_time'] = win.flip()
        et.sendTriggers(trigger['start_feed'],mode=param['resp_mode'])
        for frame in range(feed_frames):
            et.drawCompositeStim(feedback_phase)
            win.flip()
        trial_info['end_trial_time'] = core.getTime()
        trial_info['feedDur'] =  trial_info['end_trial_time']-trial_info['start_feed_time']
        
        # logging
        if trial_info['trial_count'] == 1:
            data_logger = et.Logger(outpath=output_file,nameDict = trial_info,first_columns = param['first_columns'])
        data_logger.writeTrial(trial_info)

    # end of block message
    et.sendTriggers(trigger['end_block'],mode=param['resp_mode'])
    if param['resp_mode']=='keyboard':
        event.clearEvents()
    # show text at the end of a block 
    if param['run_mode'] != 'dummy':      
        endBlock.text = param["endBlock_text"].format(block_no+1,trial_info['total_points'])
        for frame in range(pause_frames):
            endBlock.draw()
            win.flip() 
    # clear any pending key presses
    event.clearEvents()
# end of experiment message
if param['run_mode'] != 'dummy':
    endExp.text = param["endExp_text"].format(trial_info['total_points'])
    while True:
        endExp.draw()
        win.flip()
        cont=et.captureResponse(mode=param['resp_mode'],keys = [pause_resp])    
        if cont == pause_resp:
            break
#cleanup
et.finishExperiment(win,data_logger,show_results=True)
