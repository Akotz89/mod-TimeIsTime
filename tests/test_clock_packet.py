"""Exercise the clock hook against stubs on the project's guarded WSL host."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ClockPacketTest(unittest.TestCase):
    def test_clock_packet(self):
        subprocess.run(['/home/aaron/Documents/ChatGPT/wow private server/scripts/wow-build-host-guard'], check=True)
        text = (ROOT / 'src/TimeIsTime.cpp').read_text()
        start = text.index('    void OnPlayerSendInitialPacketsBeforeAddToMap(')
        end = text.index('\n    }\n};', start) + len('\n    }')
        source = r'''
#include <cmath>
#include <ctime>
#include <limits>
#include <cstdint>
#include <cstdlib>
using uint32=uint32_t; using int64=int64_t;
constexpr int SMSG_LOGIN_SETTIMESPEED=1;
bool stimeistime_enable=true; float stimeistime_speed_rate=1, stimeistime_hour_offset=0; int64 stimeistime_time_start=0;
struct Clock { int64 value; int64 count(){return value;} };
namespace GameTime { Clock now{1577836800}, uptime{60}; Clock GetGameTime(){return now;} Clock GetUptime(){return uptime;} }
struct WorldPacket { int initialized=0; time_t time=0; void Initialize(int,int){++initialized;} void AppendPackedTime(time_t t){time=t;} template<class T> WorldPacket& operator<<(T){return *this;} };
struct Session { int sent=0; void SendPacket(WorldPacket*){++sent;} };
struct Player { Session session; Session* GetSession(){return &session;} };
struct Base { virtual void OnPlayerSendInitialPacketsBeforeAddToMap(Player*,WorldPacket&){} };
struct TimeIsTime : Base {
''' + text[start:end] + r'''
};
int main(){
 setenv("TZ","UTC",1);tzset(); TimeIsTime script;
 auto run=[&](bool enabled,float speed,int64 start,float offset,time_t expected,bool shouldSend){
  stimeistime_enable=enabled;stimeistime_speed_rate=speed;stimeistime_time_start=start;stimeistime_hour_offset=offset; Player p;WorldPacket packet;
  script.OnPlayerSendInitialPacketsBeforeAddToMap(&p,packet);
  return p.session.sent==int(shouldSend) && packet.initialized==int(shouldSend) && (!shouldSend || packet.time==expected);
 };
 if(!run(true,1,0,0,1577836800,true))return 1;
 if(!run(true,2,0,0,1577836860,true))return 2;
 if(!run(true,1,1577836800,-2,1577829600,true))return 3;
 if(!run(false,1,0,0,0,false))return 4;
 if(!run(true,std::numeric_limits<float>::infinity(),0,0,0,false))return 5;
 if(!run(true,1,1577836800,std::numeric_limits<float>::quiet_NaN(),0,false))return 6;
 if(!run(true,1,915148800,0,0,false))return 7;
 if(!run(true,1,9025257600LL,0,0,false))return 8;
 if(!run(true,1,1924992000,0,1924992000,true))return 9;
 if(!run(true,1,1956528000,0,0,false))return 10;
 if(!run(true,1,-1,0,0,false))return 11;
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            cpp = Path(directory) / 'clock.cpp'
            cpp.write_text(source)
            binary = Path(directory) / 'clock'
            subprocess.run(['g++', '-std=c++17', str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)

if __name__ == '__main__':
    unittest.main()
