function: FUN_141b6f540
entry: 141b6f540
body_size: 470
signature: undefined FUN_141b6f540()


void FUN_141b6f540(longlong param_1)

{
  char cVar1;
  undefined8 uVar2;
  undefined1 auStack_88 [32];
  undefined8 local_68;
  undefined8 local_58;
  undefined8 local_50;
  undefined1 local_48;
  undefined8 local_40;
  longlong *local_38;
  undefined1 *local_30;
  longlong *local_28;
  longlong *local_20;
  undefined8 local_18;
  undefined8 local_10;
  
  local_30 = auStack_88;
  local_58 = 0;
  local_40 = 0;
  local_38 = (longlong *)0x0;
  local_28 = (longlong *)0x0;
  FUN_140dd5230(param_1);
  FUN_140e456f0(&local_38);
  local_20 = (longlong *)
             (**(code **)(*local_38 + 0x38))
                       (local_38,*(undefined8 *)(param_1 + 8),*(undefined8 *)(param_1 + 0xe8),0);
  uVar2 = (**(code **)(*local_20 + 0x38))(local_20);
  FUN_14001c140(&local_28,uVar2);
  if (local_28 == (longlong *)0x0) {
    FUN_14001e690(&local_40,&LAB_141b6d2e8);
    local_50 = *(undefined8 *)(param_1 + 0xe8);
    local_48 = 0x11;
    local_68 = 0;
    uVar2 = FUN_140053080(PTR_PTR_140dc9dc8,1,local_40,&local_50);
    FUN_140012e10(uVar2);
  }
  cVar1 = (**(code **)(*local_28 + 0x50))(local_28);
  if (cVar1 == '\0') {
    FUN_14001e690(&local_58,&LAB_141b6d2e8);
    local_50 = *(undefined8 *)(param_1 + 0xe8);
    local_48 = 0x11;
    local_68 = 0;
    uVar2 = FUN_140053080(PTR_PTR_1405208f8,1,local_58,&local_50);
    FUN_140012e10(uVar2);
  }
  local_10 = FUN_1410347f0(PTR_PTR_141033318,1);
  local_18 = FUN_1406662a0(PTR_DAT_140665a50,1);
  FUN_1406666e0(local_18,*(longlong *)(param_1 + 0xf8) + 0x540);
  FUN_141b6f3f0(auStack_88,local_28);
  FUN_140010870(local_18);
  FUN_140010870(local_10);
  FUN_140013e30(&local_58);
  FUN_140013e30(&local_40);
  FUN_14001c100(&local_38);
  FUN_14001c100(&local_28);
  return;
}


