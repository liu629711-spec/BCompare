function: FUN_140e59290
entry: 140e59290
body_size: 514
signature: undefined FUN_140e59290()


void FUN_140e59290(undefined8 param_1,undefined8 param_2,undefined8 param_3,longlong param_4,
                  char param_5)

{
  undefined4 uVar1;
  undefined8 uVar2;
  undefined1 auStack_58 [32];
  undefined8 local_38;
  undefined1 *local_30;
  longlong local_20;
  undefined8 local_18;
  longlong local_10;
  
  local_30 = auStack_58;
  local_38 = 0;
  local_18 = 0;
  local_10 = (**(code **)(param_4 + 0x18))(param_4,1);
  *(char *)(local_10 + 0x38) = param_5;
  FUN_14067ed80(local_10,param_3,0);
  FUN_140680e20(local_10,param_2,1,0);
  if (param_5 != '\0') {
    FUN_140e594a0(0,local_30);
    goto LAB_140e5947a;
  }
  FUN_1405e48a0(param_3,&local_38,L"Value");
  FUN_1405e48e0(param_2,L"Value",local_38);
  local_20 = FUN_1405e4e60(param_3,L"LastModified",0);
  if (local_20 != 0) {
    FUN_1405e48a0(local_20,&local_18,L"Value");
  }
  uVar2 = FUN_1405e4530(param_2,L"LastModified");
  FUN_1405e44f0(uVar2,L"Value",local_18);
  local_20 = FUN_1405e4e60(param_3,L"Locked",0);
  if (local_20 == 0) {
LAB_140e593cb:
    uVar1 = 0;
  }
  else {
    uVar2 = FUN_1405e45c0(local_20,L"Value");
    if ((char)uVar2 == '\0') goto LAB_140e593cb;
    uVar1 = (undefined4)CONCAT71((int7)((ulonglong)uVar2 >> 8),1);
  }
  FUN_1404fbe30(&local_18,uVar1);
  uVar2 = FUN_1405e4530(param_2,L"Locked");
  FUN_1405e4900(uVar2,L"Value",local_18,0);
  local_20 = FUN_1405e4e60(param_3,L"Summary",0);
  FUN_140013e30(&local_18);
  if (local_20 != 0) {
    FUN_1405e48a0(local_20,&local_18,L"Value");
  }
  uVar2 = FUN_1405e4530(param_2,L"Summary");
  FUN_1405e44f0(uVar2,L"Value",local_18);
  FUN_140010870(local_10);
LAB_140e5947a:
  FUN_140013e30(&local_38);
  FUN_140013e30(&local_18);
  return;
}


