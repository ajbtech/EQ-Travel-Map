import line_reader


def test_line_reader_is_line_death_positive():
    line = "[Sat Sep 24 20:41:47 2022] You have been slain by a froglok!"
    assert line_reader.is_line_death(line) is True


def test_line_reader_is_line_death_negative():
    line = "[Sat Sep 24 20:42:30 2022] A froglok hits YOU for 1 point of damage."
    assert line_reader.is_line_death(line) is False


def test_line_reader_is_line_death_null():
    line = ""
    assert line_reader.is_line_death(line) is False


def test_line_reader_is_line_login_positive():
    line = "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!"
    assert line_reader.is_line_login(line) is True


def test_line_reader_is_line_login_negative():
    line = (
        "[Sat Sep 24 20:07:28 2022] Jaranab slashes Basher Stizik "
        "for 51 points of damage."
    )
    assert line_reader.is_line_login(line) is False


def test_line_reader_is_line_kill_positive():
    line = "[Sat Sep 24 20:30:45 2022] You have slain a froglok tad!"
    assert line_reader.is_line_kill(line) is True


def test_line_reader_is_line_kill_negative():
    line = "[Sat Sep 24 20:30:45 2022] You slash a froglok tad for 6 points of damage."
    assert line_reader.is_line_kill(line) is False


def test_line_reader_is_line_kill_null():
    line = ""
    assert line_reader.is_line_kill(line) is False


def test_line_reader_is_line_level_positive():
    line = "[Sun Jan 08 14:50:01 2023] You have gained a level! Welcome to level 37!"
    assert line_reader.is_line_level(line) is True


def test_line_reader_is_line_level_negative():
    line = (
        "[Sun Jan 08 14:40:40 2023] You say out of character, "
        "'What level makes sense to do Hill Giants in Rathe?'"
    )
    assert line_reader.is_line_level(line) is False


def test_line_reader_is_line_level_null():
    line = ""
    assert line_reader.is_line_level(line) is False


def test_get_level_from_level_gained_line():
    line = "[Sun Jan 08 14:50:01 2023] You have gained a level! Welcome to level 37!"
    assert line_reader.get_level(line) == 37


def test_get_level_from_level_lost_line():
    line = "[Thu Oct 27 21:01:18 2022] You LOST a level! You are now level 19!"
    assert line_reader.get_level(line) == 19


def test_get_level_returns_none_when_line_has_no_level_event():
    line = "[Thu Oct 27 21:01:18 2022] You have lost experience."
    assert line_reader.get_level(line) is None


def test_classify_line_extracts_zone_event():
    line = "[Sun Jan 08 15:01:29 2023] You have entered Lake Rathetear."

    event = line_reader.classify_line(line)

    assert event.kind == line_reader.EventType.ZONE
    assert event.value == "Lake Rathetear"


def test_classify_line_extracts_kill_event():
    line = "[Sat Oct 29 13:05:25 2022] You have slain a ghoul!"

    event = line_reader.classify_line(line)

    assert event.kind == line_reader.EventType.KILL
    assert event.value == "ghoul"


def test_classify_line_extracts_level_lost_event():
    line = "[Thu Oct 27 21:01:18 2022] You LOST a level! You are now level 19!"

    event = line_reader.classify_line(line)

    assert event.kind == line_reader.EventType.LEVEL_LOST
    assert event.value == 19


def test_classify_line_extracts_merchant_cash_event():
    line = (
        "[Sun Jan 08 14:54:06 2023] You receive 5 platinum 1 gold "
        "2 silver 3 copper from Ulan Meadowgreen for the Fine Steel Warhammer(s)."
    )

    event = line_reader.classify_line(line)

    assert event.kind == line_reader.EventType.MERCHANT_CASH


def test_line_reader_is_line_loot_positive():
    line = "[Sun Jan 08 14:50:05 2023] --You have looted a Bronze Long Sword.--"
    assert line_reader.is_line_loot(line) is True


def test_line_reader_is_line_loot_negative():
    line = "[Tue Jan 10 22:35:28 2023] You are too far away to loot that corpse."
    assert line_reader.is_line_loot(line) is False


def test_line_reader_is_line_loot_null():
    line = ""
    assert line_reader.is_line_loot(line) is False


def test_line_reader_is_line_loot_cash_positive():
    line = (
        "[Sun Jan 08 14:51:27 2023] You receive 2 platinum, "
        "3 gold, 3 silver and 4 copper as your split."
    )
    assert line_reader.is_line_loot_cash(line) is True


def test_line_reader_is_line_loot_cash_negative():
    line = (
        "[Sun Jan 08 14:54:06 2023] You receive 5 platinum 1 gold "
        "2 silver 3 copper from Ulan Meadowgreen for the Fine Steel Warhammer(s)."
    )
    assert line_reader.is_line_loot_cash(line) is False


def test_line_reader_is_line_loot_cash_null():
    line = ""
    assert line_reader.is_line_loot_cash(line) is False


# Mob loot never exceeds ~200 of any single denomination per corpse, so
# any "You receive ..." line with a denom above that must be a self-corpse
# retrieval, not mob loot. The check is on raw per-denom counts.
def test_is_line_loot_cash_rejects_self_corpse_excess_platinum():
    line = (
        "[Sat Jan 07 14:38:52 2023] You receive 832 platinum, "
        "11 gold, 54 silver and 88 copper as your split."
    )
    assert line_reader.is_line_loot_cash(line) is False


def test_is_line_loot_cash_rejects_self_corpse_excess_gold():
    line = (
        "[Mon Oct 24 21:17:09 2022] You receive 29 platinum, "
        "398 gold and 86 silver from the corpse."
    )
    assert line_reader.is_line_loot_cash(line) is False


def test_is_line_loot_cash_rejects_self_corpse_excess_silver():
    line = (
        "[Mon Oct 24 21:17:09 2022] You receive 29 platinum, "
        "98 gold and 586 silver from the corpse."
    )
    assert line_reader.is_line_loot_cash(line) is False


def test_is_line_loot_cash_rejects_self_corpse_excess_copper():
    line = (
        "[Wed Sep 28 06:21:23 2022] You receive 16 platinum, "
        "19 gold, 49 silver and 248 copper from the corpse."
    )
    assert line_reader.is_line_loot_cash(line) is False


def test_is_line_loot_cash_allows_exactly_200():
    line = (
        "[Sat Sep 24 12:00:00 2022] You receive 200 platinum, "
        "200 gold, 200 silver and 200 copper from the corpse."
    )
    assert line_reader.is_line_loot_cash(line) is True


def test_is_line_loot_cash_allows_moderate_platinum():
    line = (
        "[Mon Oct 31 22:34:19 2022] You receive 135 platinum "
        "and 98 copper from the corpse."
    )
    assert line_reader.is_line_loot_cash(line) is True


def test_classify_line_returns_empty_for_self_corpse_loot():
    line = (
        "[Sat Jan 07 14:38:52 2023] You receive 832 platinum, "
        "11 gold, 54 silver and 88 copper as your split."
    )
    assert line_reader.classify_line(line) == line_reader.EMPTY_LINE_EVENT


def test_line_reader_is_line_merch_cash_positive():
    line = (
        "[Sun Jan 08 14:54:06 2023] You receive 5 platinum 1 gold "
        "2 silver 3 copper from Ulan Meadowgreen for the Fine Steel Warhammer(s)."
    )
    assert line_reader.is_line_merch_cash(line) is True


def test_line_reader_is_line_merch_cash_negative():
    line = (
        "[Sun Jan 08 14:51:27 2023] You receive 2 platinum, "
        "3 gold, 3 silver and 4 copper as your split."
    )
    assert line_reader.is_line_merch_cash(line) is False


def test_line_reader_is_line_merch_cash_null():
    line = ""
    assert line_reader.is_line_merch_cash(line) is False


def test_line_reader_is_line_zone_positive():
    line = "[Sun Jan 08 15:01:29 2023] You have entered Lake Rathetear."
    assert line_reader.is_line_zone(line) is True


def test_line_reader_is_line_zone_negative():
    line = "[Mon Dec 12 06:17:40 2022] You feel the spirit of wolf enter you."
    assert line_reader.is_line_zone(line) is False


def test_line_reader_is_line_zone_null():
    line = ""
    assert line_reader.is_line_zone(line) is False


def test_line_reader_is_line_level_lost_positive():
    line = "[Thu Oct 27 21:01:18 2022] You LOST a level! You are now level 19!"
    assert line_reader.is_line_level_lost(line) is True


def test_line_reader_is_line_level_lost_negative():
    line = "[Thu Oct 27 21:01:18 2022] You have lost experience."
    assert line_reader.is_line_level_lost(line) is False


def test_line_reader_is_line_level_lost_null():
    line = ""
    assert line_reader.is_line_level_lost(line) is False


def test_get_name_null():
    line = ""
    assert line_reader.get_name(line) == ""


def test_get_name_1():
    line = "[Sat Dec 10 06:30:41 2022] You have slain a Tesch Mas Gnoll!"
    assert line_reader.get_name(line) == "Tesch Mas Gnoll"


def test_get_name_2():
    line = "[Wed Oct 05 20:20:17 2022] You have slain an orc warrior!"
    assert line_reader.get_name(line) == "orc warrior"


def test_get_name_3():
    line = "[Sat Oct 01 06:45:42 2022] You have been slain by a froglok sentinel!"
    assert line_reader.get_name(line) == "froglok sentinel"


def test_get_name_4():
    line = "[Wed Oct 05 06:31:00 2022] You have been slain by Fandl Arathin!"
    assert line_reader.get_name(line) == "Fandl Arathin"


def test_get_name_5():
    line = "[Sat Oct 29 13:05:25 2022] You have slain a ghoul!"
    assert line_reader.get_name(line) == "ghoul"


def test_get_zone_1():
    line = "[Sun Jan 08 13:20:54 2023] You have entered Southern Plains of Karana."
    assert line_reader.get_zone(line) == "Southern Plains of Karana"


def test_get_zone_2():
    line = "[Sat Sep 24 19:51:48 2022] You have entered Grobb."
    assert line_reader.get_zone(line) == "Grobb"


def test_get_zone_3():
    line = "[Tue Feb 07 21:53:21 2023] You have entered The Feerrott."
    assert line_reader.get_zone(line) == "The Feerrott"


def test_get_zone_preserves_leading_article():
    # "an Arena (PvP) area" is its own log phrase; collapsing the article
    # would conflate it with the proper-noun zone "The Arena".
    line = "[Sat Mar 09 15:24:26 2024] You have entered an Arena (PvP) area."
    assert line_reader.get_zone(line) == "an Arena (PvP) area"


def test_is_line_help_positive():
    line = (
        "[Sat Sep 24 19:51:48 2022] If you need help, click on the EQ Menu "
        'button at the bottom of your screen and select the "Help" option.'
    )
    assert line_reader.is_line_help(line) is True


def test_is_line_help_negative():
    line = "[Tue Feb 07 21:53:21 2023] You have entered The Feerrott."
    assert line_reader.is_line_help(line) is False


def test_is_line_chat_says():
    line = "[Thu Oct 31 05:34:59 2024] Rezbish says, '50m'"
    assert line_reader.is_line_chat(line) is True


def test_is_line_chat_shouts():
    line = "[Thu Oct 31 05:33:05 2024] Tuxman shouts, 'GET READY 1'"
    assert line_reader.is_line_chat(line) is True


def test_is_line_chat_auctions():
    line = (
        "[Mon Oct 14 21:31:18 2024] Arastus auctions, "
        "'WTB Fungi Covered Great Staff, McMerin's Feast'"
    )
    assert line_reader.is_line_chat(line) is True


def test_is_line_chat_tells_guild():
    line = "[Mon Oct 14 21:31:23 2024] Raynbow tells the guild, 'Also, Ding! 54!'"
    assert line_reader.is_line_chat(line) is True


def test_is_line_chat_tells_group():
    line = (
        "[Thu Oct 17 21:05:15 2024] Elci tells the group, "
        "'i'd like it if you took me back to kurn's'"
    )
    assert line_reader.is_line_chat(line) is True


def test_is_line_chat_you_tell_party():
    line = (
        "[Thu Oct 17 21:05:04 2024] You tell your party, "
        "'You able to gate back or need a run?'"
    )
    assert line_reader.is_line_chat(line) is True


def test_is_line_chat_says_out_of_character():
    line = (
        "[Sun Jan 08 14:40:40 2023] You say out of character, "
        "'What level makes sense to do Hill Giants in Rathe?'"
    )
    assert line_reader.is_line_chat(line) is True


def test_is_line_chat_tells_you():
    line = "[Wed Oct 16 22:02:12 2024] Jorgaz tells you, 'inc 2'"
    assert line_reader.is_line_chat(line) is True


def test_is_line_chat_negative_zone():
    line = "[Sun Jan 08 15:01:29 2023] You have entered Lake Rathetear."
    assert line_reader.is_line_chat(line) is False


def test_is_line_chat_negative_kill():
    line = "[Sat Oct 29 13:05:25 2022] You have slain a ghoul!"
    assert line_reader.is_line_chat(line) is False


def test_is_line_chat_negative_combat():
    line = "[Sat Sep 24 20:42:30 2022] A froglok hits YOU for 1 point of damage."
    assert line_reader.is_line_chat(line) is False


def test_is_line_chat_negative_loot_cash():
    line = (
        "[Sun Jan 08 14:51:27 2023] You receive 2 platinum, "
        "3 gold, 3 silver and 4 copper as your split."
    )
    assert line_reader.is_line_chat(line) is False


def test_is_line_chat_null():
    assert line_reader.is_line_chat("") is False


def test_classify_line_returns_empty_for_chat():
    line = "[Thu Oct 31 05:34:59 2024] Rezbish says, '50m'"
    assert line_reader.classify_line(line) == line_reader.EMPTY_LINE_EVENT


def test_get_player_damage_slash():
    line = "[Sat Sep 24 20:30:45 2022] You slash a froglok tad for 6 points of damage."
    assert line_reader.get_player_damage(line) == ("slash", 6)


def test_get_player_damage_backstab():
    line = "[Sat Sep 24 20:30:45 2022] You backstab a goblin for 123 points of damage."
    assert line_reader.get_player_damage(line) == ("backstab", 123)


def test_get_player_damage_bash():
    line = "[Sat Sep 24 20:30:45 2022] You bash a skeleton for 12 points of damage."
    assert line_reader.get_player_damage(line) == ("bash", 12)


def test_get_player_damage_pierce():
    line = "[Sat Sep 24 20:30:45 2022] You pierce a gnoll for 45 points of damage."
    assert line_reader.get_player_damage(line) == ("pierce", 45)


def test_get_player_damage_singular_point():
    line = "[Sat Sep 24 20:30:45 2022] You slash a rat for 1 point of damage."
    assert line_reader.get_player_damage(line) == ("slash", 1)


def test_get_player_damage_non_melee_maps_to_spell():
    line = "You hit a goblin for 99 points of non-melee damage."
    assert line_reader.get_player_damage(line) == ("spell", 99)


def test_get_player_damage_critically_maps_to_crit():
    line = "You critically hit a troll for 200 points of damage."
    assert line_reader.get_player_damage(line) == ("crit", 200)


def test_get_player_damage_none_for_third_person():
    line = "Jaranab slashes Basher Stizik for 51 points of damage."
    assert line_reader.get_player_damage(line) is None


def test_get_player_damage_none_for_incoming_damage():
    line = "[Sat Sep 24 20:42:30 2022] A froglok hits YOU for 1 point of damage."
    assert line_reader.get_player_damage(line) is None


def test_get_player_damage_none_for_kill_line():
    line = "[Sat Sep 24 20:30:45 2022] You have slain a froglok tad!"
    assert line_reader.get_player_damage(line) is None


def test_get_player_damage_none_for_empty():
    assert line_reader.get_player_damage("") is None


def test_get_spell_cast_simple_name():
    line = "[Sat Sep 24 20:30:45 2022] You begin casting Haste."
    assert line_reader.get_spell_cast(line) == "Haste"


def test_get_spell_cast_multiword_name():
    line = "[Sat Sep 24 20:30:45 2022] You begin casting Spirit of Wolf."
    assert line_reader.get_spell_cast(line) == "Spirit of Wolf"


def test_get_spell_cast_name_with_apostrophe():
    line = "[Sat Sep 24 20:30:45 2022] You begin casting Shaman's Bulwark."
    assert line_reader.get_spell_cast(line) == "Shaman's Bulwark"


def test_get_spell_cast_none_for_non_casting_line():
    line = "[Sat Sep 24 20:30:45 2022] You slash a froglok tad for 6 points of damage."
    assert line_reader.get_spell_cast(line) is None


def test_get_spell_cast_none_for_kill_line():
    line = "[Sat Sep 24 20:30:45 2022] You have slain a froglok tad!"
    assert line_reader.get_spell_cast(line) is None


def test_get_spell_cast_none_for_empty():
    assert line_reader.get_spell_cast("") is None
