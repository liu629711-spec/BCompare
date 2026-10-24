function: FUN_140e74100
entry: 140e74100
body_size: 1364
signature: undefined FUN_140e74100()


void FUN_140e74100(longlong param_1,int param_2,int param_3,int *param_4,int *param_5,byte param_6)

{
  int *piVar1;
  int *piVar2;
  bool bVar3;
  int iVar4;
  longlong lVar5;
  int iVar6;
  int iVar7;
  int iVar8;
  undefined1 auStack_88 [32];
  int *local_68;
  undefined1 local_60;
  int local_54;
  int *local_50;
  int local_48;
  int local_44;
  int local_40;
  int local_3c;
  int local_30;
  int local_2c [3];
  
  local_54 = param_2;
  local_50 = param_4;
  local_48 = param_3;
  if (0 < *(int *)(param_1 + 0x88)) {
    if (param_6 == 0) {
      iVar6 = *(int *)(param_1 + 0x88);
      local_40 = 0;
      if (-1 < iVar6 + -1) {
        do {
          piVar1 = (int *)(*(longlong *)(param_1 + 0x90) + (longlong)local_40 * 0x10);
          iVar7 = *piVar1;
          if ((*local_50 < piVar1[2] + iVar7) || (*param_5 < piVar1[3] + iVar7)) {
            iVar4 = *local_50 - piVar1[2];
            if (iVar7 <= *local_50 - piVar1[2]) {
              iVar4 = iVar7;
            }
            *piVar1 = iVar4;
            iVar7 = *param_5 - piVar1[3];
            if (*piVar1 <= *param_5 - piVar1[3]) {
              iVar7 = *piVar1;
            }
            *piVar1 = iVar7;
            FUN_140e74080(auStack_88);
          }
          local_40 = local_40 + 1;
          iVar6 = iVar6 + -1;
        } while (iVar6 != 0);
      }
    }
    FUN_140e73f30(auStack_88,0,*(int *)(param_1 + 0x88) + -1);
    iVar6 = *(int *)(param_1 + 0x88);
    local_40 = 0;
    if (-1 < iVar6 + -1) {
      do {
        piVar1 = (int *)(*(longlong *)(param_1 + 0x90) + (longlong)local_40 * 0x10);
        if (0 < piVar1[1]) {
          bVar3 = false;
          local_2c[0] = piVar1[2] + *piVar1 + -1;
          local_30 = piVar1[3] + *piVar1 + -1;
          local_3c = local_40 + 1;
          iVar7 = *(int *)(param_1 + 0x88) + -1;
          if (local_3c <= iVar7) {
            iVar7 = (iVar7 - local_3c) + 1;
            do {
              piVar2 = (int *)(*(longlong *)(param_1 + 0x90) + (longlong)local_3c * 0x10);
              if (0 < piVar2[1]) {
                iVar4 = piVar2[2] + *piVar2 + -1;
                iVar8 = piVar2[3] + *piVar2 + -1;
                if (((piVar2[2] <= local_2c[0]) || (piVar2[3] <= local_30)) &&
                   ((piVar1[2] <= iVar4 || (piVar1[3] <= iVar8)))) {
                  if ((((piVar2[2] < piVar1[2]) && (piVar2[3] < piVar1[3])) &&
                      ((piVar1[2] <= iVar4 || (piVar1[3] <= iVar8)))) &&
                     ((iVar4 < local_2c[0] && (iVar8 < local_30)))) {
                    iVar4 = piVar1[2] - piVar2[2];
                    if (piVar1[3] - piVar2[3] <= piVar1[2] - piVar2[2]) {
                      iVar4 = piVar1[3] - piVar2[3];
                    }
                    *piVar2 = iVar4;
                    FUN_140e74080(auStack_88,piVar2);
                    bVar3 = true;
                  }
                  else if (((piVar1[2] < piVar2[2]) && (piVar1[3] < piVar2[3])) &&
                          ((((piVar2[2] <= local_2c[0] || (piVar2[3] <= local_30)) &&
                            (local_2c[0] < iVar4)) && (local_30 < iVar8)))) {
                    local_44 = (local_2c[0] - piVar2[2]) + 1;
                    iVar4 = (local_30 - piVar2[3]) + 1;
                    if (local_44 <= iVar4) {
                      local_44 = iVar4;
                    }
                    *piVar2 = *piVar2 - local_44;
                    piVar2[2] = piVar2[2] + local_44;
                    piVar2[3] = piVar2[3] + local_44;
                    FUN_140e74080(auStack_88,piVar2);
                    bVar3 = true;
                  }
                  else {
                    piVar2[1] = -1;
                  }
                }
              }
              local_3c = local_3c + 1;
              iVar7 = iVar7 + -1;
            } while (iVar7 != 0);
          }
          if (bVar3) {
            FUN_140e73f30(auStack_88,local_40 + 1,*(int *)(param_1 + 0x88) + -1);
          }
        }
        local_40 = local_40 + 1;
        iVar6 = iVar6 + -1;
      } while (iVar6 != 0);
    }
    FUN_140e73d30(auStack_88,0,*(int *)(param_1 + 0x88) + -1);
  }
  local_44 = 0;
  iVar6 = *(int *)(param_1 + 0x88);
  local_40 = 0;
  if (iVar6 - 1U < 0x80000000) {
    do {
      lVar5 = (longlong)local_40;
      if (0 < *(int *)(*(longlong *)(param_1 + 0x90) + 4 + lVar5 * 0x10)) {
        local_44 = local_44 + 1;
        local_2c[0] = *(int *)(*(longlong *)(param_1 + 0x90) + 8 + lVar5 * 0x10) + -1;
        local_30 = *(int *)(*(longlong *)(param_1 + 0x90) + 0xc + lVar5 * 0x10) + -1;
        if ((local_54 <= local_2c[0]) || (local_48 <= local_30)) {
          local_68 = &local_30;
          local_60 = 0;
          FUN_140e74660(param_1,local_54,local_48,local_2c);
        }
        lVar5 = (longlong)local_40;
        FUN_140e71e30(param_1,*(undefined4 *)(*(longlong *)(param_1 + 0x90) + 8 + lVar5 * 0x10),
                      *(undefined4 *)(*(longlong *)(param_1 + 0x90) + 0xc + lVar5 * 0x10),
                      *(undefined4 *)(*(longlong *)(param_1 + 0x90) + lVar5 * 0x10));
        local_54 = *(int *)(*(longlong *)(param_1 + 0x90) + 8 + lVar5 * 0x10) +
                   *(int *)(*(longlong *)(param_1 + 0x90) + lVar5 * 0x10);
        local_48 = *(int *)(*(longlong *)(param_1 + 0x90) + 0xc + lVar5 * 0x10) +
                   *(int *)(*(longlong *)(param_1 + 0x90) + lVar5 * 0x10);
      }
      local_40 = local_40 + 1;
      iVar6 = iVar6 + -1;
    } while (iVar6 != 0);
  }
  if ((param_6 & 0 < local_44) == 0) {
    if ((local_54 <= *local_50) || (local_48 <= *param_5)) {
      if ((param_6 == 0) || ((*local_50 < local_54 || (*param_5 < local_48)))) {
        local_60 = 0;
      }
      else {
        local_60 = 1;
      }
      local_68 = param_5;
      FUN_140e74660(param_1,local_54,local_48,local_50);
    }
  }
  else {
    *local_50 = local_54 + -1;
    *param_5 = local_48 + -1;
  }
  return;
}


