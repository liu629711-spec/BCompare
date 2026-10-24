object SccChooseProviderDialog: TSccChooseProviderDialog
  Caption = 'Provider'
  ClientHeight = 207
  ClientWidth = 323
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object ProviderLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Choose source control &provider:'
    FocusControl = ProviderListBox
  end
  object ProviderListBox: TUiListBox
    Left = 8
    Top = 25
    Width = 307
    Height = 143
    TabOrder = 0
    OnDblClick = ProviderListBoxDblClick
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 168
    Width = 323
    TabOrder = 1
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
