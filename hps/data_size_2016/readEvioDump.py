import os
import sys
import re

N_TI_WORDS = 6
N_SVT_HEADER_WORDS = 2 # header and tail, per roc
N_MS_HEADER_WORDS = 4 # per roc
MIN_SVT_ROC_BANK=51
MAX_SVT_ROC_BANK=66



from ROOT import TH1F, TCanvas

def match_event_bank_header(s):
    #m = re.match('.*<event format.*count=\"(\d+)\".*data_type=\"0x10\" tag=\"136\".*num=\"204\".*length=\"(\d+)\" ndata=\"(\d+)\"> ',s)
    m = re.match('.*<event format.*count=\"(\d+)\".*.*length=\"(\d+)\".*ndata=\"(\d+)\".*',s)
    return m

def match_svt_roc_bank_header(s):
    #<bank content="bank" data_type="0xe" tag="51" padding="0" num="1" length="16" ndata="14">
    m = re.match('.*<bank content=\"bank\" data_type=\"0xe\" tag=\"(\d+)\" padding=\"0\" num=\"(\d+)\" length=\"(\d+)\" ndata=\"(\d+)\">.*',s)
    if m != None:
        if int(m.group(1)) < MIN_SVT_ROC_BANK or int(m.group(1)) > MAX_SVT_ROC_BANK:
            m = None
    return m

def match_svt_bank_header(s):
    #<uint32 data_type="0x1" tag="3" padding="0" num="51" length="8" ndata="6">
    m = re.match('.*<uint32 data_type=\"0x1\" tag=\"3\" padding=\"0\" num=\"(\d+)\" length=\"(\d+)\" ndata=\"(\d+)\".*',s)
    if m != None:
        if int(m.group(1)) < MIN_SVT_ROC_BANK or int(m.group(1)) > MAX_SVT_ROC_BANK:
            m = None

    return m


def plot_event_size(file_name,max_events):
    
    h = TH1F('h_event_size','Event size(' + file_name + ');Event evio bank length (bytes);Entries',100,0,25000)
    h_svt_roc = TH1F('h_svt_roc','SVT Roc Event size(' + file_name + ');SVT Roc evio bank length (bytes);Entries',100,0,3000)
    h_svt_roc_total = TH1F('h_svt_roc_total','SVT All Roc Event size(' + file_name + ');SVT All Roc evio bank length (bytes);Entries',100,0,25000)
    h_svt_data = TH1F('h_svt_data','SVT Data Roc size(' + file_name + ');SVT data per Roc size (bytes);Entries',100,0,3000)
    h_svt_data_total = TH1F('h_svt_data_total','SVT Data total size(' + file_name + ');SVT data total size (bytes);Entries',100,0,10000)
    h_svt_nhits_total = TH1F('h_svt_nhits_total','SVT hits total (' + file_name + ');SVT hits;Entries',500,0,500)
    h_svt_rocs = TH1F('h_svt_rocs','SVT ROCs in event (' + file_name + ');SVT ROCs;Entries',20,0,20)
    n_svt_roc_words = -1
    n_svt_words = -1
    n_svt_hits = -1
    roc_ids = []
    with open(file_name,'r') as f:
        for line in f:
            #print 'Line :\"', line.rstrip(), '\"'
            m_event = match_event_bank_header(line.rstrip())
            if m_event != None:
                #print 'Matched event bank to line ', line.rstrip()
                event_nr = m_event.group(1)
                length = m_event.group(2)
                ndata = m_event.group(3)
                if event_nr < 10:
                    continue
                #print 'event_nr ', event_nr, ' length ', length, ' ndata ', ndata
                h.Fill(int(length)*4)
                if int(event_nr) > max_events:
                    break
                # fill svt data size
                if n_svt_words != -1:
                    h_svt_data_total.Fill(n_svt_words*4)
                if n_svt_roc_words != -1:
                    h_svt_roc_total.Fill(n_svt_roc_words*4)
                if n_svt_hits != -1:
                    h_svt_nhits_total.Fill(n_svt_hits)
                if roc_ids:
                    #print roc_ids
                    h_svt_rocs.Fill(len(roc_ids))
                # reset svt event size
                n_svt_words = 0 
                n_svt_roc_words = 0 
                n_svt_hits = 0
                roc_ids = []
            
            m_event = match_svt_roc_bank_header(line.rstrip())
            if m_event != None:
                #print 'Matched svt roc bank to line ', line.rstrip()
                roc_nr = m_event.group(1)
                svt_event_nr = m_event.group(2)
                length = m_event.group(3)
                ndata = m_event.group(4)
                #print 'event_nr ', event_nr, ' length ', length, ' ndata ', ndata
                h_svt_roc.Fill(int(length)*4)
                n_svt_roc_words += int(length)
                roc_ids.append(int(roc_nr))
            
            m_event = match_svt_bank_header(line.rstrip())
            if m_event != None:
                #print 'Matched svt bank to line ', line.rstrip()
                roc_nr = m_event.group(1)
                length = m_event.group(2)
                ndata = m_event.group(3)
                #print 'event_nr ', event_nr, ' length ', length, ' ndata ', ndata
                h_svt_data.Fill(int(ndata)*4)            
                n_svt_words += int(ndata)
                n = int(ndata) - N_SVT_HEADER_WORDS - N_MS_HEADER_WORDS
                n_svt_hits += n/4 # four words per hit
            
    c = TCanvas('event_size','event_size',10,10,700,500)
    h.Draw()
    #c.SetLogy()
    c.SaveAs(os.path.splitext(os.path.basename(file_name))[0] + '_event_size.png')
    
    c_svt_roc = TCanvas('event_size_svt_roc','event_size_svt_roc',10,10,700,500)
    h_svt_roc.Draw()
    #c_svt_roc.SetLogy()
    c_svt_roc.SaveAs(os.path.splitext(os.path.basename(file_name))[0] + '_event_size_svt_roc.png')

    c_svt_roc_total = TCanvas('event_size_svt_roc_all','event_size_svt_roc_all',10,10,700,500)
    h_svt_roc_total.Draw()
    #c_svt_roc_total.SetLogy()
    c_svt_roc_total.SaveAs(os.path.splitext(os.path.basename(file_name))[0] + '_event_size_svt_roc_all.png')
    
    c_svt_data = TCanvas('event_size_svt_data','event_size_svt_data',10,10,700,500)
    h_svt_data.Draw()
    #c_svt_data.SetLogy()
    c_svt_data.SaveAs(os.path.splitext(os.path.basename(file_name))[0] + '_event_size_svt_data.png')
    
    c_svt_data_total = TCanvas('event_size_svt_data_total','event_size_svt_data_total',10,10,700,500)
    h_svt_data_total.Draw()
    #c_svt_data_total.SetLogy()    
    c_svt_data_total.SaveAs(os.path.splitext(os.path.basename(file_name))[0] + '_event_size_total.png')
    
    c_svt_nhits_total = TCanvas('svt_nhits_total','svt_nhits_total',10,10,700,500)
    h_svt_nhits_total.Draw()
    #c_svt_nhits_total.SetLogy()
    c_svt_nhits_total.SaveAs(os.path.splitext(os.path.basename(file_name))[0] + '_svt_nhits_total.png')

    c_svt_rocs = TCanvas('svt_rocs','svt_rocs',10,10,700,500)
    h_svt_rocs.Draw()
    #c_svt_rocs.SetLogy()
    c_svt_rocs.SaveAs(os.path.splitext(os.path.basename(file_name))[0] + '_svt_rocs.png')

    ans = raw_input('continue?')



if __name__ == '__main__':
    print 'Just Go'

    plot_event_size(sys.argv[1],10000)

