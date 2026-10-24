object VfsGenerateSSLCertDialog: TVfsGenerateSSLCertDialog
  Caption = 'Generate Self-signed SSL Certificate'
  ClientHeight = 407
  ClientWidth = 313
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object KeyLengthLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Key &length in bits:'
    FocusControl = KeyLengthEdit
  end
  object ExpirationLbl: TUiLabel
    Left = 164
    Top = 8
    Height = 13
    Caption = 'E&xpiration:'
    FocusControl = ExpirationEdit
  end
  object CommonNameLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = '&Common name:'
    FocusControl = CommonNameEdit
  end
  object OrganizationLbl: TUiLabel
    Left = 8
    Top = 100
    Height = 13
    Caption = '&Organization:'
    FocusControl = OrganizationEdit
  end
  object OrganizationalUnitLbl: TUiLabel
    Left = 8
    Top = 146
    Height = 13
    Caption = 'Organizational &unit:'
    FocusControl = OrganizationalUnitEdit
  end
  object CityLbl: TUiLabel
    Left = 8
    Top = 192
    Height = 13
    Caption = 'Ci&ty:'
    FocusControl = CityEdit
  end
  object StateLbl: TUiLabel
    Left = 8
    Top = 238
    Height = 13
    Caption = '&State/Province:'
    FocusControl = StateEdit
  end
  object CountryLbl: TUiLabel
    Left = 264
    Top = 238
    Height = 13
    Caption = 'Cou&ntry:'
    FocusControl = CountryEdit
  end
  object EmailLbl: TUiLabel
    Left = 8
    Top = 284
    Height = 13
    Caption = '&Email:'
    FocusControl = EmailEdit
  end
  object OutputFilenameLbl: TUiLabel
    Left = 8
    Top = 330
    Height = 13
    Caption = 'Output &filename:'
    FocusControl = OutputFilenameEdit
  end
  object KeyLengthEdit: TUiComboBox
    Left = 8
    Top = 25
    Width = 67
    Height = 21
    Style = csDropDownList
    MaxLength = 4
    TabOrder = 0
    OnChange = SomethingChangedClick
  end
  object ExpirationEdit: TUiDateTimePicker
    Left = 164
    Top = 25
    Width = 141
    Height = 21
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
  object CommonNameEdit: TUiEdit
    Left = 8
    Top = 71
    Width = 297
    Height = 21
    TabOrder = 2
    OnChange = SomethingChangedClick
  end
  object OrganizationEdit: TUiEdit
    Left = 8
    Top = 117
    Width = 297
    Height = 21
    TabOrder = 3
    OnChange = SomethingChangedClick
  end
  object OrganizationalUnitEdit: TUiEdit
    Left = 8
    Top = 163
    Width = 297
    Height = 21
    TabOrder = 4
    Text = 'Beyond Compare user'
    OnChange = SomethingChangedClick
  end
  object CityEdit: TUiEdit
    Left = 8
    Top = 209
    Width = 297
    Height = 21
    TabOrder = 5
    OnChange = SomethingChangedClick
  end
  object StateEdit: TUiEdit
    Left = 8
    Top = 255
    Width = 241
    Height = 21
    TabOrder = 6
    OnChange = SomethingChangedClick
  end
  object CountryEdit: TUiEdit
    Left = 264
    Top = 255
    Width = 41
    Height = 21
    MaxLength = 2
    TabOrder = 7
    OnChange = SomethingChangedClick
  end
  object EmailEdit: TUiEdit
    Left = 8
    Top = 301
    Width = 297
    Height = 21
    TabOrder = 8
    OnChange = SomethingChangedClick
  end
  object OutputFilenameEdit: TUiSpecBar
    Left = 8
    Top = 347
    Width = 297
    TabOrder = 9
    OnBrowse = OutputFilenameEditBrowse
    OnChange = SomethingChangedClick
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 368
    Width = 313
    TabOrder = 10
    object OkBtn: TUiOkBtn
      Caption = '&Generate'
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
