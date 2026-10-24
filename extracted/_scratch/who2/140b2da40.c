function: FUN_140b2da40
entry: 140b2da40
body_size: 757
signature: undefined FUN_140b2da40()


void FUN_140b2da40(longlong param_1)

{
  longlong lVar1;
  undefined1 auStack_a8 [32];
  longlong *local_88;
  char *local_80;
  undefined8 local_78;
  undefined8 local_70;
  int local_64;
  undefined1 *local_60;
  char local_4d;
  int local_4c;
  longlong local_48;
  longlong local_40;
  longlong local_38;
  longlong *local_30;
  
  local_60 = auStack_a8;
  FUN_140b2d340(*(undefined8 *)(param_1 + 0x80));
  if ((*(longlong *)(*(longlong *)(param_1 + 0x80) + 0xd0) != 0) &&
     ((*(ulonglong *)(*(longlong *)(param_1 + 0x80) + 0x2a0) & 0xffffffffffff0000) != 0)) {
    local_64 = FUN_140b1b5f0();
    local_4c = 0;
    if (-1 < local_64 + -1) {
      do {
        local_40 = 0;
        local_48 = 0;
        local_4d = '\0';
        lVar1 = FUN_140b1b600(*(undefined8 *)(*(longlong *)(param_1 + 0x80) + 0xd0),local_4c);
        local_88 = &local_48;
        local_80 = &local_4d;
        (**(code **)(*(longlong *)(param_1 + 0x80) + 0x2a0))
                  (*(undefined8 *)(*(longlong *)(param_1 + 0x80) + 0x2a8),
                   *(undefined8 *)(param_1 + 0x80),*(undefined8 *)(lVar1 + 0x30),&local_40);
        if (local_40 != 0) {
          if (local_4d != '\0') {
            FUN_140129af0(*(undefined8 *)(*(longlong *)(param_1 + 0x80) + 0x298),local_40);
          }
          if (local_48 != 0) {
            local_30 = (longlong *)
                       FUN_140b1a6c0(PTR_PTR_140af7770,1,
                                     *(undefined1 *)(*(longlong *)(param_1 + 0x80) + 0xda));
            (**(code **)(*local_30 + 8))(local_30,local_48);
            FUN_140129af0(*(undefined8 *)(*(longlong *)(param_1 + 0x80) + 0x298),local_30);
            local_38 = FUN_140b2d680(PTR_LAB_140b1d400,1,0);
            lVar1 = *(longlong *)(param_1 + 0x80);
            *(undefined8 *)(local_38 + 0x1e8) = *(undefined8 *)(lVar1 + 0x1e8);
            *(undefined8 *)(local_38 + 0x1f0) = *(undefined8 *)(lVar1 + 0x1f0);
            lVar1 = *(longlong *)(param_1 + 0x80);
            *(undefined8 *)(local_38 + 0x1f8) = *(undefined8 *)(lVar1 + 0x1f8);
            *(undefined8 *)(local_38 + 0x200) = *(undefined8 *)(lVar1 + 0x200);
            lVar1 = *(longlong *)(param_1 + 0x80);
            *(undefined8 *)(local_38 + 0x208) = *(undefined8 *)(lVar1 + 0x208);
            *(undefined8 *)(local_38 + 0x210) = *(undefined8 *)(lVar1 + 0x210);
            lVar1 = *(longlong *)(param_1 + 0x80);
            *(undefined8 *)(local_38 + 0x218) = *(undefined8 *)(lVar1 + 0x218);
            *(undefined8 *)(local_38 + 0x220) = *(undefined8 *)(lVar1 + 0x220);
            local_88 = *(longlong **)(*(longlong *)(param_1 + 0x80) + 0xe8);
            local_80 = (char *)0x0;
            local_78 = *(undefined8 *)(*(longlong *)(param_1 + 0x80) + 0xf8);
            local_70 = 0;
            FUN_140b2dd90(local_38,local_30,0,*(undefined8 *)(*(longlong *)(param_1 + 0x80) + 0xe0))
            ;
            FUN_140129af0(*(undefined8 *)(*(longlong *)(param_1 + 0x80) + 0x298),local_38);
          }
        }
        local_4c = local_4c + 1;
        local_64 = local_64 + -1;
      } while (local_64 != 0);
    }
  }
  return;
}


