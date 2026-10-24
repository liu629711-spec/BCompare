object VfsFtpProfileListingFrame: TVfsFtpProfileListingFrame
  HelpType = htKeyword
  HelpKeyword = 'ProfileFtpListing'
  Caption = 'Listings'
  object LinkResolutionPanel: TUiPanel
    Left = 0
    Top = 25
    Width = 255
    Height = 71
    BevelOuter = bvNone
    TabOrder = 1
    object LinkResolutionLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'Link resolution:'
    end
    object FastEdit: TUiRadioButton
      Left = 8
      Top = 25
      Height = 17
      Caption = '&Fast'
      TabOrder = 0
      OnClick = SomethingChangedClick
    end
    object SimpleEdit: TUiRadioButton
      Left = 8
      Top = 46
      Height = 17
      Caption = '&Simple'
      TabOrder = 1
      OnClick = SomethingChangedClick
    end
  end
  object ListOptionsPanel: TUiPanel
    Left = 0
    Top = 96
    Width = 255
    Height = 155
    BevelOuter = bvNone
    TabOrder = 2
    object ListOptionsLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'LIST options:'
    end
    object UseMLSDEdit: TUiCheckBox
      Left = 8
      Top = 25
      Height = 17
      Caption = 'Use &MLSD command'
      TabOrder = 0
      OnClick = SomethingChangedClick
    end
    object ShowHiddenEdit: TUiCheckBox
      Left = 8
      Top = 46
      Height = 17
      Caption = 'Show &hidden [-a]'
      TabOrder = 1
      OnClick = SomethingChangedClick
    end
    object ForceLongFormatEdit: TUiCheckBox
      Left = 8
      Top = 67
      Height = 17
      Caption = 'F&orce long format [-l]'
      TabOrder = 2
      OnClick = SomethingChangedClick
    end
    object CompleteTimestampsEdit: TUiCheckBox
      Left = 8
      Top = 88
      Height = 17
      Caption = 'Complete &timestamps [-T]'
      TabOrder = 3
      OnClick = SomethingChangedClick
    end
    object ResolveLinksEdit: TUiCheckBox
      Left = 8
      Top = 109
      Height = 17
      Caption = 'Resolve &links [-L]'
      TabOrder = 4
      OnClick = SomethingChangedClick
    end
    object RecursiveEdit: TUiCheckBox
      Left = 8
      Top = 130
      Height = 17
      Caption = '&Recursive [-R]'
      TabOrder = 5
      OnClick = SomethingChangedClick
    end
  end
  object MiscPanel: TUiPanel
    Left = 0
    Top = 251
    Width = 255
    Height = 54
    BevelOuter = bvNone
    TabOrder = 3
    object HideVMSVersionsEdit: TUiCheckBox
      Left = 8
      Top = 8
      Height = 17
      Caption = 'Hide &VMS versions'
      TabOrder = 0
      OnClick = SomethingChangedClick
    end
    object FetchIncompleteTimestampsEdit: TUiCheckBox
      Left = 8
      Top = 29
      Height = 17
      Caption = 'F&etch incomplete timestamps'
      TabOrder = 1
      OnClick = SomethingChangedClick
    end
  end
end
