object FileView: TFileView
  object JobProgressPanel: TUiPanel
    Left = 0
    Top = 642
    Width = 750
    Height = 21
    Align = alBottom
    TabOrder = 0
    object JobCancelBtn: TUiSpeedButton
      Left = 4
      Top = 2
      Width = 17
      Height = 17
      Hint = 'Stop Loading|Terminates comparison.'
      ImageIndex = imgStopRed
      Images = BcImages.MainImages
      OnClick = JobCancelClick
    end
    object JobProgressBar: TUiProgressBar
      Left = 28
      Top = 4
      Width = 657
      Height = 13
      State = pbsMarquee
      TabOrder = 0
    end
  end
  object JobErrorPanel: TUiPanel
    Left = 0
    Top = 663
    Width = 750
    Height = 21
    Align = alBottom
    TabOrder = 1
    object JobErrorImage: TUiImage
      Left = 4
      Top = 2
      Width = 16
      Height = 16
      ImageIndex = imgError
      Images = BcImages.MainImages
    end
    object JobErrorLbl: TUiLabel
      Left = 24
      Top = 4
      Height = 13
      Caption = '%'
    end
  end
  object MessagePanel: TUiPanel
    TabOrder = 2
  end
  object StatusBar: TUiStatusBar
    Panels = <
      item
        Style = psOwnerDraw
        Width = 225
        Images = BcImages.ContentImages
      end
      item
        Width = 225
      end
    >
  end
  object SpecInfoPopup: TUiPopupMenu
    Left = 32
  end
end
