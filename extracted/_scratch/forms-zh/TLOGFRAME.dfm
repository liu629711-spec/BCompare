object LogFrame: TLogFrame
  Left = 0
  Top = 0
  Width = 702
  Height = 100
  TabOrder = 0
  object LeftPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 21
    Height = 100
    Align = alLeft
    BevelOuter = bvNone
    TabOrder = 0
    object OptionsBtn: TUiSpeedButton
      Left = 2
      Top = 2
      Width = 18
      Height = 18
      Hint = 'Log Options|Changes handling of log messages.'
      ImageIndex = imgOptions
      Images = BcImages.MainImages
      OnClick = OptionsClick
    end
    object SaveBtn: TUiSpeedButton
      Left = 2
      Top = 22
      Width = 18
      Height = 18
      Hint = 'Save Log|Saves log messages to file.'
      ImageIndex = imgSave
      Images = BcImages.MainImages
      OnClick = SaveClick
    end
  end
  object ListBox: TUiVirtualListBox
    Left = 21
    Top = 0
    Width = 681
    Height = 100
    Align = alClient
    TabOrder = 1
    TabStop = False
    OnDrawPrep = ListBoxDrawPrep
    OnGetText = ListBoxGetText
  end
end
