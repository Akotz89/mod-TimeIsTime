/*
 * Azerothcore Module:     TimeIsTime
 * Author:                 Dunjeon
 * Contributing Author(s): lasyan3, vratam @ RegWorks
 * Version:                20250608
 * License:                GNU Affero General Public License v3.0.
 */

#include "ScriptMgr.h"
#include "Player.h"
#include "Config.h"
#include "Chat.h"
#include "GameTime.h"

#include <cmath>
#include <ctime>
#include <limits>

static bool   stimeistime_enable,
              stimeistime_announce;
static float  stimeistime_speed_rate,
              stimeistime_hour_offset;
static int64  stimeistime_time_start;

class TimeIsTimeBeforeConfigLoad : public WorldScript {
public:

    TimeIsTimeBeforeConfigLoad() : WorldScript("TimeIsTimeBeforeConfigLoad") { }

    void OnBeforeConfigLoad(bool /*reload*/) override {
        stimeistime_enable = sConfigMgr->GetOption<bool>("TimeIsTime.Enable", true);
        stimeistime_announce = sConfigMgr->GetOption<bool>("TimeIsTime.Announce", true);
        stimeistime_speed_rate = sConfigMgr->GetOption<float>("TimeIsTime.SpeedRate", 1.0);
        stimeistime_hour_offset = sConfigMgr->GetOption<float>("TimeIsTime.HourOffset", 0.0);
        stimeistime_time_start = sConfigMgr->GetOption<int64>("TimeIsTime.TimeStart", 0);
    }
};

class TimeIsTime : public PlayerScript {
public:

    TimeIsTime() : PlayerScript("TimeIsTime") { }

    void OnPlayerLogin(Player* player) {
        if (stimeistime_enable && stimeistime_announce)
            ChatHandler(player->GetSession()).SendSysMessage("This server is running the |cff4CFF00TimeIsTime |rmodule");
    }
	
    void OnPlayerSendInitialPacketsBeforeAddToMap(Player* player, WorldPacket& data) override {
        if (!stimeistime_enable || stimeistime_time_start < 0)
            return;

        double const now = double(GameTime::GetGameTime().count());
        double const uptime = double(GameTime::GetUptime().count());
        double const timestamp = stimeistime_time_start > 0
            ? double(stimeistime_time_start) + double(stimeistime_hour_offset) * 3600.0
            : now + uptime * (double(stimeistime_speed_rate) - 1.0);
        if (!std::isfinite(stimeistime_speed_rate) || !std::isfinite(timestamp) ||
            timestamp < double(std::numeric_limits<time_t>::lowest()) ||
            timestamp >= double(std::numeric_limits<time_t>::max()))
            return;

        time_t const clientTime = time_t(timestamp);
        std::tm calendar{};
#if defined(_WIN32) || defined(_WIN64)
        if (localtime_s(&calendar, &clientTime) != 0)
#else
        if (!localtime_r(&clientTime, &calendar))
#endif
            return;
        // The packed-time year uses five bits relative to 2000.
        if (calendar.tm_year < 100 || calendar.tm_year > 131)
            return; // Retain the core's already-sent default clock packet.

        data.Initialize(SMSG_LOGIN_SETTIMESPEED, 4 + 4 + 4);
        data.AppendPackedTime(clientTime);
        data << float(0.01666667f) * stimeistime_speed_rate;
        data << uint32(0);

        player->GetSession()->SendPacket(&data);
    }
};

void AddTimeIsTimeScripts() {
    new TimeIsTimeBeforeConfigLoad();
    new TimeIsTime();
}
