function: FUN_140e74b60
entry: 140e74b60
body_size: 3728
signature: undefined FUN_140e74b60()


void FUN_140e74b60(longlong param_1,int param_2,int param_3,int param_4,int param_5)

{
  char cVar1;
  int iVar2;
  int iVar3;
  longlong lVar4;
  uint local_res10;
  int local_res18;
  int local_res20 [2];
  undefined1 auStack_148 [32];
  undefined4 *local_128;
  undefined1 local_120;
  undefined1 *local_110;
  int local_104;
  longlong local_100;
  undefined8 local_f8;
  longlong local_f0;
  longlong local_e8;
  bool local_dd;
  int local_dc;
  longlong local_d8;
  longlong local_d0;
  longlong local_c8;
  longlong local_c0;
  longlong local_b8;
  char local_a9;
  longlong local_a8;
  longlong local_a0;
  bool local_91;
  longlong local_90;
  longlong local_88;
  longlong local_80;
  int local_74;
  longlong local_70;
  longlong local_68;
  longlong local_60;
  longlong local_58;
  longlong local_50;
  int local_44;
  int local_40;
  uint local_3c;
  int local_38;
  int local_34;
  int local_30;
  int local_2c;
  undefined8 local_28;
  undefined8 local_20;
  
  local_110 = auStack_148;
  local_50 = 0;
  local_58 = 0;
  local_60 = 0;
  local_68 = 0;
  local_70 = 0;
  local_res20[0] = param_4;
  for (local_2c = 0; (param_2 + local_2c <= local_res20[0] && (param_3 + local_2c <= param_5));
      local_2c = local_2c + 1) {
    iVar2 = FUN_140e72e80(param_1,0,param_2 + local_2c);
    iVar3 = FUN_140e72e80(param_1,1,param_3 + local_2c);
    if (iVar2 != iVar3) break;
  }
  FUN_140e71e30(param_1,param_2,param_3,local_2c);
  local_res10 = param_2 + local_2c;
  local_res18 = param_3 + local_2c;
  for (local_44 = 0;
      ((int)local_res10 <= local_res20[0] - local_44 && (local_res18 <= param_5 - local_44));
      local_44 = local_44 + 1) {
    iVar2 = FUN_140e72e80(param_1,0,local_res20[0] - local_44);
    iVar3 = FUN_140e72e80(param_1,1,param_5 - local_44);
    if (iVar2 != iVar3) break;
  }
  local_res20[0] = local_res20[0] - local_44;
  param_5 = param_5 - local_44;
  if ((local_res20[0] < (int)local_res10) || (param_5 < local_res18)) {
    FUN_140e71e30(param_1,local_res10,0xffffffff,(local_res20[0] - local_res10) + 1);
    FUN_140e71e30(param_1,0xffffffff,local_res18,(param_5 - local_res18) + 1);
    FUN_140e71e30(param_1,local_res20[0] + 1,param_5 + 1,local_44);
  }
  else {
    FUN_140019870(&local_68,PTR_DAT_140006b80,1,(longlong)((param_5 - local_res18) + 1));
    local_80 = local_68;
    if (local_68 != 0) {
      local_80 = *(longlong *)(local_68 + -8);
    }
    iVar2 = (int)local_80;
    local_30 = 0;
    if (-1 < iVar2 + -1) {
      do {
        *(undefined4 *)(local_68 + (longlong)local_30 * 4) = 0xffffffff;
        local_30 = local_30 + 1;
        iVar2 = iVar2 + -1;
      } while (iVar2 != 0);
    }
    local_74 = 0;
    local_28 = FUN_140526440(PTR_PTR_140522748,1);
    local_3c = local_res10;
    if ((int)local_res10 <= local_res20[0]) {
      iVar2 = (local_res20[0] - local_res10) + 1;
      do {
        FUN_140ddfb30(*(undefined8 *)(param_1 + 8));
        local_34 = FUN_140e72e80(param_1,0,local_3c);
        if (local_34 != -1) {
          cVar1 = FUN_140528450(local_28,local_34);
          if (cVar1 == '\0') {
            FUN_140528420(local_28,local_34,local_3c);
          }
          else {
            FUN_140528510(local_28,local_34,0xffffffff);
            local_74 = local_74 + 1;
          }
        }
        local_3c = local_3c + 1;
        iVar2 = iVar2 + -1;
      } while (iVar2 != 0);
    }
    local_20 = FUN_140526440(PTR_PTR_140522748,1);
    local_40 = local_res18;
    if (local_res18 <= param_5) {
      iVar2 = (param_5 - local_res18) + 1;
      do {
        FUN_140ddfb30(*(undefined8 *)(param_1 + 8));
        local_34 = FUN_140e72e80(param_1,1,local_40);
        cVar1 = FUN_140528480(local_28,local_34,&local_3c);
        if ((cVar1 != '\0') && (local_3c != 0xffffffff)) {
          cVar1 = FUN_140528450(local_20,local_34);
          if (cVar1 == '\0') {
            FUN_140528420(local_20,local_34,local_40);
            *(uint *)(local_68 + (longlong)(local_40 - local_res18) * 4) = local_3c;
          }
          else {
            iVar3 = FUN_1405284f0(local_20,local_34);
            *(undefined4 *)(local_68 + (longlong)(iVar3 - local_res18) * 4) = 0xffffffff;
            FUN_1405284d0(local_28,local_34);
          }
        }
        local_40 = local_40 + 1;
        iVar2 = iVar2 + -1;
      } while (iVar2 != 0);
    }
    FUN_140010870(local_20);
    FUN_140010870(local_28);
    FUN_140019870(&local_50,PTR_DAT_140006b80,1,(longlong)((param_5 - local_res18) + 1));
    local_88 = local_50;
    if (local_50 != 0) {
      local_88 = *(longlong *)(local_50 + -8);
    }
    iVar2 = (int)local_88;
    local_30 = 0;
    if (-1 < iVar2 + -1) {
      do {
        *(undefined4 *)(local_50 + (longlong)local_30 * 4) = 0xffffffff;
        local_30 = local_30 + 1;
        iVar2 = iVar2 + -1;
      } while (iVar2 != 0);
    }
    FUN_140019a50(&local_60,PTR_DAT_140006b80);
    FUN_140019a50(&local_58,PTR_DAT_140006b80);
    local_38 = 0;
    local_40 = local_res18;
    if (local_res18 <= param_5) {
      iVar2 = (param_5 - local_res18) + 1;
      do {
        FUN_140ddfb30(*(undefined8 *)(param_1 + 8));
        local_3c = *(uint *)(local_68 + (longlong)(local_40 - local_res18) * 4);
        if (local_3c != 0xffffffff) {
          if (local_60 == 0) {
            local_91 = false;
          }
          else {
            local_90 = local_60;
            if (local_60 != 0) {
              local_90 = *(longlong *)(local_60 + -8);
            }
            local_91 = *(int *)(local_60 + -4 + local_90 * 4) < (int)local_3c;
          }
          if (local_91 == false) {
            if ((local_60 == 0) || ((int)local_3c <= *(int *)(local_60 + (longlong)local_38 * 4))) {
              local_a9 = '\0';
            }
            else {
              local_a8 = local_60;
              if (local_60 != 0) {
                local_a8 = *(longlong *)(local_60 + -8);
              }
              if (((longlong)local_38 == local_a8 + -1) ||
                 ((int)local_3c < *(int *)(local_60 + (longlong)(local_38 + 1) * 4))) {
                local_a9 = '\x01';
              }
              else {
                local_a9 = '\0';
              }
            }
            if (local_a9 == '\0') {
              local_38 = 0;
              while( true ) {
                local_b8 = local_60;
                if (local_60 != 0) {
                  local_b8 = *(longlong *)(local_60 + -8);
                }
                if ((local_b8 <= local_38) ||
                   ((int)local_3c <= *(int *)(local_60 + (longlong)local_38 * 4))) break;
                local_38 = local_38 + 1;
              }
            }
            else {
              local_38 = local_38 + 1;
            }
          }
          else {
            local_a0 = local_60;
            if (local_60 != 0) {
              local_a0 = *(longlong *)(local_60 + -8);
            }
            local_38 = (int)local_a0;
          }
          if (0 < local_38) {
            *(undefined4 *)(local_50 + (longlong)(local_40 - local_res18) * 4) =
                 *(undefined4 *)(local_58 + (longlong)(local_38 + -1) * 4);
          }
          local_c0 = local_60;
          if (local_60 != 0) {
            local_c0 = *(longlong *)(local_60 + -8);
          }
          lVar4 = (longlong)local_38;
          if (lVar4 == local_c0) {
            FUN_140019870(&local_60,PTR_DAT_140006b80,1,(longlong)(local_38 + 1));
            FUN_140019870(&local_58,PTR_DAT_140006b80,1,(longlong)(local_38 + 1));
          }
          *(uint *)(local_60 + lVar4 * 4) = local_3c;
          *(int *)(local_58 + lVar4 * 4) = local_40;
        }
        local_40 = local_40 + 1;
        iVar2 = iVar2 + -1;
      } while (iVar2 != 0);
    }
    if (local_60 == 0) {
      if (*(char *)(param_1 + 0xac) == '\0') {
        if ((int)(local_res20[0] - local_res10) < param_5 - local_res18) {
          local_104 = local_res20[0] - local_res10;
        }
        else {
          local_104 = param_5 - local_res18;
        }
        local_2c = local_104 + 1;
        cVar1 = (**(code **)(**(longlong **)(param_1 + 0x10) + 0x20))
                          (*(longlong **)(param_1 + 0x10));
        if (cVar1 == '\0') {
          FUN_140e71e30(param_1,local_res10,local_res18,local_2c);
          local_res10 = local_res10 + local_2c;
          local_res18 = local_res18 + local_2c;
        }
        FUN_140e71e30(param_1,local_res10,0xffffffff,(local_res20[0] - local_res10) + 1);
        FUN_140e71e30(param_1,0xffffffff,local_res18,(param_5 - local_res18) + 1);
      }
      else {
        if (local_74 < 0x3e9) {
          if (param_5 - local_res18 < (int)(local_res20[0] - local_res10)) {
            local_dc = local_res20[0] - local_res10;
          }
          else {
            local_dc = param_5 - local_res18;
          }
          local_dd = 5000 < local_dc;
        }
        else {
          local_dd = true;
        }
        if (local_dd == false) {
          *(uint *)(param_1 + 0x84) = (local_res20[0] - local_res10) + 1;
          *(int *)(param_1 + 0x5c) = (param_5 - local_res18) + 1;
          FUN_140019870(param_1 + 0xa0,PTR_DAT_140e71488,1,(longlong)(*(int *)(param_1 + 0x84) + 1))
          ;
          local_e8 = *(longlong *)(param_1 + 0xa0);
          local_f0 = local_e8;
          if (local_e8 != 0) {
            local_f0 = *(longlong *)(local_e8 + -8);
          }
          iVar2 = (int)local_f0;
          local_30 = 0;
          if (-1 < iVar2 + -1) {
            do {
              FUN_140019870(*(longlong *)(param_1 + 0xa0) + (longlong)local_30 * 8,PTR_DAT_140e71438
                            ,1,(longlong)(*(int *)(param_1 + 0x5c) + 1));
              local_f8 = *(undefined8 *)(*(longlong *)(param_1 + 0xa0) + (longlong)local_30 * 8);
              local_100 = (longlong)(*(int *)(param_1 + 0x5c) + 1);
              FUN_14000dce0(local_f8,local_100,0);
              local_30 = local_30 + 1;
              iVar2 = iVar2 + -1;
            } while (iVar2 != 0);
          }
          local_128 = &param_5;
          local_120 = 0;
          FUN_140e74660(param_1,local_res10,local_res18,local_res20);
          FUN_140019a50(param_1 + 0xa0,PTR_DAT_140e71488);
        }
        else {
          local_128 = (undefined4 *)CONCAT44(local_128._4_4_,param_5);
          FUN_140e73b40(param_1,local_res10,local_res18,local_res20[0]);
        }
      }
    }
    else {
      FUN_140019a50(&local_70,PTR_DAT_140e74b00);
      local_c8 = local_58;
      if (local_58 != 0) {
        local_c8 = *(longlong *)(local_58 + -8);
      }
      for (local_40 = *(int *)(local_58 + -4 + local_c8 * 4); local_40 != -1;
          local_40 = *(int *)(local_50 + (longlong)(local_40 - local_res18) * 4)) {
        local_d0 = local_70;
        if (local_70 != 0) {
          local_d0 = *(longlong *)(local_70 + -8);
        }
        local_30 = (int)local_d0;
        FUN_140019870(&local_70,PTR_DAT_140e74b00,1,(longlong)((int)local_d0 + 1));
        *(undefined4 *)(local_70 + (longlong)local_30 * 8) =
             *(undefined4 *)(local_68 + (longlong)(local_40 - local_res18) * 4);
        *(int *)(local_70 + 4 + (longlong)local_30 * 8) = local_40;
      }
      local_d8 = local_70;
      if (local_70 != 0) {
        local_d8 = *(longlong *)(local_70 + -8);
      }
      local_30 = (int)local_d8 + -1;
      local_40 = -1;
      if (-1 < local_30) {
        do {
          lVar4 = (longlong)local_30;
          if (((int)local_res10 < *(int *)(local_70 + lVar4 * 8)) ||
             (local_res18 < *(int *)(local_70 + 4 + lVar4 * 8))) {
            local_128 = (undefined4 *)
                        CONCAT44(local_128._4_4_,*(int *)(local_70 + 4 + lVar4 * 8) + -1);
            FUN_140e74b60(param_1,local_res10,local_res18,*(int *)(local_70 + lVar4 * 8) + -1);
          }
          FUN_140e71e30(param_1,*(undefined4 *)(local_70 + lVar4 * 8),
                        *(undefined4 *)(local_70 + 4 + lVar4 * 8),1);
          local_res10 = *(int *)(local_70 + lVar4 * 8) + 1;
          local_res18 = *(int *)(local_70 + 4 + lVar4 * 8) + 1;
          local_30 = local_30 + -1;
        } while (local_30 != -1);
      }
      local_128 = (undefined4 *)CONCAT44(local_128._4_4_,param_5);
      FUN_140e74b60(param_1,local_res10,local_res18,local_res20[0]);
    }
    FUN_140e71e30(param_1,local_res20[0] + 1,param_5 + 1,local_44);
  }
  FUN_140019a50(&local_70,PTR_DAT_140e74b00);
  FUN_140017970(&local_68,PTR_DAT_140006b80,4);
  return;
}


