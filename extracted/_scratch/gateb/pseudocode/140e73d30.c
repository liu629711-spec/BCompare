function: FUN_140e73d30
entry: 140e73d30
body_size: 325
signature: undefined FUN_140e73d30()


void FUN_140e73d30(longlong param_1,uint param_2,uint param_3)

{
  undefined8 *puVar1;
  undefined8 *puVar2;
  undefined8 uVar3;
  undefined8 uVar4;
  int iVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  uint local_50;
  
  local_50 = param_2;
  do {
    uVar8 = local_50 + param_3 >> 1;
    uVar6 = local_50;
    uVar7 = param_3;
    do {
      while (iVar5 = FUN_140e73cc0(param_1,uVar6,uVar8), iVar5 < 0) {
        uVar6 = uVar6 + 1;
      }
      while (iVar5 = FUN_140e73cc0(param_1,uVar7,uVar8), 0 < iVar5) {
        uVar7 = uVar7 - 1;
      }
      if ((int)uVar6 <= (int)uVar7) {
        puVar1 = (undefined8 *)
                 (*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + (longlong)(int)uVar6 * 0x10)
        ;
        uVar3 = *puVar1;
        uVar4 = puVar1[1];
        puVar1 = (undefined8 *)
                 (*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + (longlong)(int)uVar6 * 0x10)
        ;
        puVar2 = (undefined8 *)
                 (*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + (longlong)(int)uVar7 * 0x10)
        ;
        *puVar1 = *puVar2;
        puVar1[1] = puVar2[1];
        puVar1 = (undefined8 *)
                 (*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + (longlong)(int)uVar7 * 0x10)
        ;
        *puVar1 = uVar3;
        puVar1[1] = uVar4;
        uVar9 = uVar7;
        if ((uVar8 != uVar6) && (uVar9 = uVar8, uVar8 == uVar7)) {
          uVar9 = uVar6;
        }
        uVar6 = uVar6 + 1;
        uVar7 = uVar7 - 1;
        uVar8 = uVar9;
      }
    } while ((int)uVar6 <= (int)uVar7);
    if ((int)local_50 < (int)uVar7) {
      FUN_140e73d30(param_1,local_50,uVar7);
    }
    local_50 = uVar6;
  } while ((int)uVar6 < (int)param_3);
  return;
}


