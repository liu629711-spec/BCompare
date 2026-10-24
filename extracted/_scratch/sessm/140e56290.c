function: FUN_140e56290
entry: 140e56290
body_size: 115
signature: undefined FUN_140e56290()


void FUN_140e56290(longlong *param_1,undefined8 param_2)

{
  char cVar1;
  undefined8 uVar2;
  
  FUN_140680e00(param_1,param_2);
  if ((char)param_1[7] == '\0') {
    uVar2 = FUN_140504ff0();
    FUN_140e5d0b0(DAT_141ff70e8,param_2,uVar2);
    FUN_140e5d480(DAT_141ff70e8,param_2,1);
    cVar1 = (**(code **)(*param_1 + 0x188))(*param_1);
    if (cVar1 == '\x04') {
      FUN_140e5dd30(DAT_141ff70e8,param_2,L"Dummy");
    }
  }
  return;
}


